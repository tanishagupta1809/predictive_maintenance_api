# -*- coding: utf-8 -*-
"""
Utility functions for predictive maintenance ML pipeline
Provides data loading, preprocessing, and validation utilities
"""

import numpy as np
import pandas as pd
import logging
from typing import Tuple, Dict, List, Any
from sklearn.preprocessing import StandardScaler
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataValidator:
    """Validates input data for machine learning predictions"""

    # Define valid ranges for each feature
    VALID_RANGES = {
        'Air temperature [K]': (295, 305),
        'Process temperature [K]': (305, 320),
        'Rotational speed [rpm]': (1168, 9009),
        'Torque [Nm]': (3.8, 76.6),
        'Tool wear [min]': (0, 254)
    }

    VALID_TYPES = ['H', 'M', 'L']  # High, Medium, Low quality types

    @staticmethod
    def validate_input(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate input data for prediction
        
        Args:
            data: Input dictionary with machine parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = [
                'air_temp', 'process_temp', 'speed', 'torque', 'tool_wear', 'type'
            ]
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"

            # Validate air temperature
            air_temp = float(data['air_temp'])
            if not DataValidator.VALID_RANGES['Air temperature [K]'][0] <= air_temp <= DataValidator.VALID_RANGES['Air temperature [K]'][1]:
                return False, f"Air temperature out of range: {DataValidator.VALID_RANGES['Air temperature [K]']}"

            # Validate process temperature
            process_temp = float(data['process_temp'])
            if not DataValidator.VALID_RANGES['Process temperature [K]'][0] <= process_temp <= DataValidator.VALID_RANGES['Process temperature [K]'][1]:
                return False, f"Process temperature out of range: {DataValidator.VALID_RANGES['Process temperature [K]']}"

            # Validate speed
            speed = float(data['speed'])
            if not DataValidator.VALID_RANGES['Rotational speed [rpm]'][0] <= speed <= DataValidator.VALID_RANGES['Rotational speed [rpm]'][1]:
                return False, f"Rotational speed out of range: {DataValidator.VALID_RANGES['Rotational speed [rpm]']}"

            # Validate torque
            torque = float(data['torque'])
            if not DataValidator.VALID_RANGES['Torque [Nm]'][0] <= torque <= DataValidator.VALID_RANGES['Torque [Nm]'][1]:
                return False, f"Torque out of range: {DataValidator.VALID_RANGES['Torque [Nm]']}"

            # Validate tool wear
            tool_wear = float(data['tool_wear'])
            if not DataValidator.VALID_RANGES['Tool wear [min]'][0] <= tool_wear <= DataValidator.VALID_RANGES['Tool wear [min]'][1]:
                return False, f"Tool wear out of range: {DataValidator.VALID_RANGES['Tool wear [min]']}"

            # Validate type
            machine_type = str(data['type']).upper()
            if machine_type not in DataValidator.VALID_TYPES:
                return False, f"Type must be one of: {DataValidator.VALID_TYPES}"

            return True, ""

        except (ValueError, TypeError) as e:
            return False, f"Invalid data type: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class DataPreprocessor:
    """Handles data preprocessing for ML pipeline"""

    @staticmethod
    def load_dataset(file_path: str) -> pd.DataFrame:
        """Load dataset from CSV file"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            raise

    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create feature matrix from dataframe"""
        feature_cols = [
            'Air temperature [K]',
            'Process temperature [K]',
            'Rotational speed [rpm]',
            'Torque [Nm]',
            'Tool wear [min]',
            'Type'
        ]

        # Verify all features exist
        missing_cols = [col for col in feature_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            raise ValueError(f"Missing required columns: {missing_cols}")

        X = df[feature_cols].copy()

        # Check for missing values
        if X.isnull().any().any():
            logger.warning("Missing values detected in features, filling with median")
            X = X.fillna(X.median(numeric_only=True))

        return X

    @staticmethod
    def get_fault_type(row: pd.Series) -> str:
        """Determine fault type from binary fault columns"""
        fault_cols = ['TWF', 'HDF', 'PWF', 'OSF', 'RNF']

        for col in fault_cols:
            if col in row.index and row[col] == 1:
                return col

        return 'No Failure'

    @staticmethod
    def encode_and_scale(X: pd.DataFrame, scaler: StandardScaler = None) -> Tuple[np.ndarray, StandardScaler, List[str]]:
        """
        Encode categorical variables and scale features
        
        Returns:
            Tuple of (scaled_features, scaler, feature_columns)
        """
        # One-hot encode categorical variables
        X_encoded = pd.get_dummies(X, drop_first=False)
        feature_columns = X_encoded.columns.tolist()

        # Scale features
        if scaler is None:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_encoded)
        else:
            X_scaled = scaler.transform(X_encoded)

        logger.info(f"Features encoded and scaled: {X_scaled.shape}")

        return X_scaled, scaler, feature_columns


class ModelEvaluator:
    """Evaluates model performance with comprehensive metrics"""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_pred_proba: np.ndarray = None) -> Dict[str, float]:
        """
        Calculate comprehensive evaluation metrics
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities (optional)
            
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            roc_auc_score, confusion_matrix, balanced_accuracy_score
        )

        # Determine if this is binary or multiclass classification
        unique_classes = len(np.unique(y_true))
        average_method = 'binary' if unique_classes == 2 else 'weighted'

        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average=average_method, zero_division=0),
            'recall': recall_score(y_true, y_pred, average=average_method, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average=average_method, zero_division=0),
            'balanced_accuracy': balanced_accuracy_score(y_true, y_pred)
        }

        # Calculate ROC-AUC if probabilities are available
        if y_pred_proba is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba[:, 1])
            except Exception as e:
                logger.warning(f"Could not calculate ROC-AUC: {str(e)}")

        # Calculate confusion matrix components
        cm = confusion_matrix(y_true, y_pred)
        if len(cm) == 2:
            tn, fp, fn, tp = cm.ravel()
            metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
            metrics['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0

        return metrics

    @staticmethod
    def get_feature_importance(model, feature_names: List[str], top_n: int = 10) -> pd.DataFrame:
        """Extract and return top feature importances"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feat_importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)

            return feat_importance_df.head(top_n)
        return None

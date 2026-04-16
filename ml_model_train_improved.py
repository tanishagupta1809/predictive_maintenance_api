# -*- coding: utf-8 -*-
"""
Improved ML Model Training Pipeline
Includes hyperparameter tuning, cross-validation, and comprehensive evaluation
"""

import pandas as pd
import numpy as np
import joblib
import logging
import os
from typing import Dict, Tuple, Any
import kagglehub

from sklearn.model_selection import train_test_split, cross_validate, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from ml_utils import DataPreprocessor, ModelEvaluator, DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictiveMaintenanceTrainer:
    """Training pipeline for predictive maintenance models"""

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.preprocessor = DataPreprocessor()
        self.evaluator = ModelEvaluator()

    def download_dataset(self) -> str:
        """Download dataset from Kaggle"""
        try:
            logger.info("Downloading dataset...")
            path = kagglehub.dataset_download(
                "stephanmatzka/predictive-maintenance-dataset-ai4i-2020"
            )
            csv_path = os.path.join(path, "ai4i2020.csv")
            logger.info(f"Dataset downloaded to: {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"Error downloading dataset: {str(e)}")
            raise

    def prepare_data(self, csv_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, 
                                                    StandardScaler, list, pd.DataFrame]:
        """Load and preprocess data"""
        logger.info("Loading and preprocessing data...")

        # Load dataset
        df = self.preprocessor.load_dataset(csv_path)

        # Check class distribution
        class_distribution = df['Machine failure'].value_counts()
        logger.info(f"Class distribution:\n{class_distribution}")
        logger.info(f"Class imbalance ratio: {class_distribution[1] / class_distribution[0]:.4f}")

        # Create features
        X = self.preprocessor.create_features(df)

        # Add fault type classification
        df['Failure Type'] = df.apply(self.preprocessor.get_fault_type, axis=1)

        # Get labels
        y_failure = df['Machine failure'].values
        y_fault = df['Failure Type'].values

        # Encode and scale
        X_scaled, scaler, feature_columns = self.preprocessor.encode_and_scale(X)

        logger.info(f"Data preparation complete: {X_scaled.shape[0]} samples, {X_scaled.shape[1]} features")

        return X_scaled, y_failure, y_fault, scaler, feature_columns, df

    def train_failure_model(self, X_train: np.ndarray, X_test: np.ndarray,
                           y_train: np.ndarray, y_test: np.ndarray,
                           feature_columns: list) -> Dict[str, Any]:
        """Train and optimize failure prediction model"""
        logger.info("Training failure prediction model...")

        # Use stratified split to handle class imbalance
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [8, 10, 12, 15],
            'min_samples_split': [5, 10],
            'min_samples_leaf': [2, 4],
            'class_weight': ['balanced', 'balanced_subsample']
        }

        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)

        # Grid search with cross-validation
        logger.info("Running hyperparameter tuning (GridSearchCV)...")
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=5,
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X_train, y_train)

        best_model = grid_search.best_estimator_
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best cross-validation F1 score: {grid_search.best_score_:.4f}")

        # Evaluate on test set
        y_pred = best_model.predict(X_test)
        y_pred_proba = best_model.predict_proba(X_test)

        metrics = self.evaluator.calculate_metrics(y_test, y_pred, y_pred_proba)

        logger.info("\nFailure Model Performance:")
        for metric_name, metric_value in metrics.items():
            logger.info(f"  {metric_name}: {metric_value:.4f}")

        # Feature importance
        feat_importance = self.evaluator.get_feature_importance(best_model, feature_columns, top_n=15)
        logger.info("\nTop 15 Feature Importances:")
        logger.info(feat_importance.to_string())

        # Classification report
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred, target_names=['No Failure', 'Failure']))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"\nConfusion Matrix:\n{cm}")

        return {
            'model': best_model,
            'metrics': metrics,
            'confusion_matrix': cm,
            'best_params': grid_search.best_params_,
            'feature_importance': feat_importance
        }

    def train_fault_type_model(self, X_train: np.ndarray, X_test: np.ndarray,
                              y_train: np.ndarray, y_test: np.ndarray,
                              feature_columns: list) -> Dict[str, Any]:
        """Train fault type classification model"""
        logger.info("Training fault type classification model...")

        # Filter only failure samples
        failure_mask_train = y_train != 'No Failure'
        failure_mask_test = y_test != 'No Failure'

        X_fault_train = X_train[failure_mask_train]
        y_fault_filtered_train = y_train[failure_mask_train]

        X_fault_test = X_test[failure_mask_test]
        y_fault_filtered_test = y_test[failure_mask_test]

        if len(np.unique(y_fault_filtered_train)) < 2:
            logger.warning("Not enough failure types in training data for fault classification")
            return None

        # Encode fault types
        fault_encoder = LabelEncoder()
        y_fault_encoded_train = fault_encoder.fit_transform(y_fault_filtered_train)
        y_fault_encoded_test = fault_encoder.transform(y_fault_filtered_test)

        logger.info(f"Fault classes: {fault_encoder.classes_}")
        logger.info(f"Training samples: {len(y_fault_encoded_train)}, Test samples: {len(y_fault_encoded_test)}")

        # Hyperparameter tuning for fault model
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [10, 15],
            'class_weight': ['balanced']
        }

        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)

        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=3,
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )

        grid_search.fit(X_fault_train, y_fault_encoded_train)
        best_model = grid_search.best_estimator_

        logger.info(f"Best parameters for fault model: {grid_search.best_params_}")

        # Evaluate
        y_pred = best_model.predict(X_fault_test)
        metrics = self.evaluator.calculate_metrics(y_fault_encoded_test, y_pred)

        logger.info("\nFault Type Model Performance:")
        for metric_name, metric_value in metrics.items():
            logger.info(f"  {metric_name}: {metric_value:.4f}")

        logger.info("\nClassification Report:")
        logger.info(classification_report(y_fault_encoded_test, y_pred, target_names=fault_encoder.classes_))

        return {
            'model': best_model,
            'encoder': fault_encoder,
            'metrics': metrics,
            'best_params': grid_search.best_params_
        }

    def save_models(self, failure_model: dict, fault_model: dict, 
                   scaler: StandardScaler, feature_columns: list):
        """Save trained models and preprocessing objects"""
        logger.info("Saving models and preprocessing objects...")

        joblib.dump(failure_model['model'], os.path.join(self.model_dir, "failure_model.pkl"))
        joblib.dump(scaler, os.path.join(self.model_dir, "scaler.pkl"))
        joblib.dump(feature_columns, os.path.join(self.model_dir, "feature_columns.pkl"))

        if fault_model:
            joblib.dump(fault_model['model'], os.path.join(self.model_dir, "fault_model.pkl"))
            joblib.dump(fault_model['encoder'], os.path.join(self.model_dir, "fault_encoder.pkl"))

        # Save metadata
        metadata = {
            'failure_model_metrics': failure_model['metrics'],
            'fault_model_metrics': fault_model['metrics'] if fault_model else None,
            'feature_columns': feature_columns,
            'training_date': pd.Timestamp.now().isoformat()
        }

        joblib.dump(metadata, os.path.join(self.model_dir, "model_metadata.pkl"))
        logger.info(f"Models saved to {self.model_dir}")

    def plot_results(self, failure_model: dict, fault_model: dict = None):
        """Create visualizations of model performance"""
        logger.info("Creating performance visualizations...")

        # Failure model confusion matrix
        cm = failure_model['confusion_matrix']
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.title('Failure Prediction - Confusion Matrix')
        plt.tight_layout()
        plt.savefig(os.path.join(self.model_dir, 'failure_confusion_matrix.png'), dpi=100)
        logger.info("Saved confusion matrix plot")

        # Feature importance
        if failure_model['feature_importance'] is not None:
            plt.figure(figsize=(10, 6))
            feat_imp = failure_model['feature_importance'].sort_values('importance')
            plt.barh(feat_imp['feature'], feat_imp['importance'])
            plt.xlabel('Importance')
            plt.title('Top Features - Failure Prediction Model')
            plt.tight_layout()
            plt.savefig(os.path.join(self.model_dir, 'feature_importance.png'), dpi=100)
            logger.info("Saved feature importance plot")

    def run_full_pipeline(self, csv_path: str = None):
        """Run complete training pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Predictive Maintenance Model Training Pipeline")
        logger.info("=" * 60)

        try:
            # Download dataset if not provided
            if csv_path is None:
                csv_path = self.download_dataset()

            # Prepare data
            X_scaled, y_failure, y_fault, scaler, feature_columns, df = self.prepare_data(csv_path)

            # Split data
            X_train, X_test, y_failure_train, y_failure_test, y_fault_train, y_fault_test = train_test_split(
                X_scaled, y_failure, y_fault,
                test_size=0.2,
                random_state=42,
                stratify=y_failure
            )

            logger.info(f"Data split: {X_train.shape[0]} training, {X_test.shape[0]} test samples")

            # Train failure model
            failure_model = self.train_failure_model(
                X_train, X_test, y_failure_train, y_failure_test, feature_columns
            )

            # Train fault type model
            fault_model = self.train_fault_type_model(
                X_train, X_test, y_fault_train, y_fault_test, feature_columns
            )

            # Save models
            self.save_models(failure_model, fault_model, scaler, feature_columns)

            # Create visualizations
            self.plot_results(failure_model, fault_model)

            logger.info("=" * 60)
            logger.info("Training pipeline completed successfully!")
            logger.info("=" * 60)

            return failure_model, fault_model

        except Exception as e:
            logger.error(f"Error in training pipeline: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    trainer = PredictiveMaintenanceTrainer(model_dir="./models")
    trainer.run_full_pipeline()

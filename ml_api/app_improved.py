"""
Improved Predictive Maintenance API
Enhanced with validation, logging, error handling, and comprehensive response metadata
"""

from flask import Flask, request, jsonify, Response
import joblib
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple
import os
from datetime import datetime
import json

from ml_utils import DataValidator, DataPreprocessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Model configuration
MODEL_VERSION = "1.0"
MODEL_DIR = "./models"

# Global model variables
failure_model = None
fault_model = None
fault_encoder = None
scaler = None
feature_columns = None
model_metadata = None
model_loaded = False

# Adjust model directory to parent directory if running from ml_api
if not os.path.exists(MODEL_DIR) and os.path.exists("../models"):
    MODEL_DIR = "../models"


def load_models():
    """Load trained models and preprocessing objects"""
    global failure_model, fault_model, fault_encoder, scaler, feature_columns, model_metadata, model_loaded

    try:
        if not model_loaded:
            logger.info("Loading models...")

            failure_model = joblib.load(os.path.join(MODEL_DIR, "failure_model.pkl"))
            scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
            feature_columns = joblib.load(os.path.join(MODEL_DIR, "feature_columns.pkl"))

            # Load optional models
            try:
                fault_model = joblib.load(os.path.join(MODEL_DIR, "fault_model.pkl"))
                fault_encoder = joblib.load(os.path.join(MODEL_DIR, "fault_encoder.pkl"))
            except FileNotFoundError:
                logger.warning("Fault model not found, fault classification disabled")

            # Load metadata
            try:
                model_metadata = joblib.load(os.path.join(MODEL_DIR, "model_metadata.pkl"))
            except FileNotFoundError:
                logger.warning("Model metadata not found")
                model_metadata = {}

            model_loaded = True
            logger.info("Models loaded successfully")
            return True

    except Exception as e:
        logger.error(f"Error loading models: {str(e)}", exc_info=True)
        return False


def prepare_input(data: Dict[str, Any]) -> Tuple[bool, Any, str]:
    """
    Prepare input data for prediction
    
    Returns:
        Tuple of (success, prepared_data, error_message)
    """
    try:
        # Validate input
        is_valid, error_msg = DataValidator.validate_input(data)
        if not is_valid:
            return False, None, error_msg

        # Create input dataframe
        base_input = {
            'Air temperature [K]': float(data["air_temp"]),
            'Process temperature [K]': float(data["process_temp"]),
            'Rotational speed [rpm]': float(data["speed"]),
            'Torque [Nm]': float(data["torque"]),
            'Tool wear [min]': float(data["tool_wear"]),
            'Type': str(data["type"]).upper()
        }

        input_df = pd.DataFrame([base_input])

        # Encode features
        input_encoded = pd.get_dummies(input_df)

        # Ensure all feature columns are present
        for col in feature_columns:
            if col not in input_encoded.columns:
                input_encoded[col] = 0

        # Reorder columns to match training data
        input_encoded = input_encoded[feature_columns]

        # Scale features
        input_scaled = scaler.transform(input_encoded)

        return True, input_scaled, ""

    except Exception as e:
        logger.error(f"Error preparing input: {str(e)}", exc_info=True)
        return False, None, f"Error preparing input: {str(e)}"


def create_response(success: bool, data: Dict[str, Any] = None, 
                   error: str = None, status_code: int = 200) -> Tuple[Response, int]:
    """Create standardized API response"""
    response_data = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "data": data if success else None,
        "error": error if not success else None
    }

    return jsonify(response_data), status_code


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "Predictive Maintenance API",
        "version": MODEL_VERSION,
        "models_loaded": model_loaded
    })


@app.route("/health", methods=["GET"])
def health():
    """Comprehensive health check"""
    health_data = {
        "status": "healthy" if model_loaded else "unhealthy",
        "models_loaded": model_loaded,
        "timestamp": datetime.utcnow().isoformat()
    }

    if model_loaded and model_metadata:
        health_data["model_metadata"] = {
            "training_date": model_metadata.get("training_date"),
            "failure_model_metrics": model_metadata.get("failure_model_metrics"),
            "features_count": len(feature_columns)
        }

    status_code = 200 if model_loaded else 503
    return jsonify(health_data), status_code


@app.route("/predict", methods=["POST"])
def predict():
    """
    Predict machine failure and fault type
    
    Expected JSON input:
    {
        "air_temp": float,
        "process_temp": float,
        "speed": float,
        "torque": float,
        "tool_wear": float,
        "type": string (H/M/L)
    }
    """
    if not model_loaded:
        return create_response(False, error="Models not loaded", status_code=503)

    try:
        data = request.json

        if not data:
            return create_response(False, error="No JSON data provided", status_code=400)

        logger.info(f"Prediction request received: {data}")

        # Prepare input
        success, input_scaled, error_msg = prepare_input(data)
        if not success:
            logger.warning(f"Input preparation failed: {error_msg}")
            return create_response(False, error=error_msg, status_code=400)

        # Failure prediction
        failure_pred = failure_model.predict(input_scaled)[0]
        failure_proba = failure_model.predict_proba(input_scaled)[0]
        
        # Get confidence (higher of the two probabilities)
        failure_confidence = float(max(failure_proba))
        no_failure_confidence = float(failure_proba[0])
        failure_confidence_val = float(failure_proba[1])

        response_data = {
            "failure_predicted": int(failure_pred),
            "failure_confidence": round(failure_confidence_val, 4),
            "no_failure_confidence": round(no_failure_confidence, 4),
            "risk_level": get_risk_level(failure_confidence_val, failure_pred),
            "recommendations": get_recommendations(failure_pred, failure_confidence_val)
        }

        # Fault type prediction if failure predicted
        if failure_pred == 1 and fault_model is not None:
            try:
                fault_pred_encoded = fault_model.predict(input_scaled)[0]
                fault_pred = fault_encoder.inverse_transform([fault_pred_encoded])[0]
                fault_proba = fault_model.predict_proba(input_scaled)[0]
                fault_confidence = float(max(fault_proba))

                fault_map = {
                    "HDF": "Heat Dissipation Failure",
                    "TWF": "Tool Wear Failure",
                    "PWF": "Power Failure",
                    "OSF": "Overstrain Failure",
                    "RNF": "Random Component Failure"
                }

                response_data["fault_type"] = fault_map.get(str(fault_pred), str(fault_pred))
                response_data["fault_type_code"] = str(fault_pred)
                response_data["fault_confidence"] = round(fault_confidence, 4)

                logger.info(f"Fault predicted: {fault_pred} with confidence {fault_confidence:.4f}")

            except Exception as e:
                logger.warning(f"Error in fault prediction: {str(e)}")
                response_data["fault_type"] = "Unknown"
                response_data["fault_confidence"] = 0.0
        else:
            response_data["fault_type"] = "No Failure"
            response_data["fault_type_code"] = "NO_FAILURE"
            response_data["fault_confidence"] = 0.0

        logger.info(f"Prediction successful: failure={failure_pred}, confidence={failure_confidence_val:.4f}")
        return create_response(True, data=response_data)

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return create_response(False, error=f"Prediction failed: {str(e)}", status_code=500)


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Batch prediction for multiple machines
    
    Expected JSON input:
    {
        "predictions": [
            {...single prediction object...},
            ...
        ]
    }
    """
    if not model_loaded:
        return create_response(False, error="Models not loaded", status_code=503)

    try:
        data = request.json

        if not data or "predictions" not in data:
            return create_response(False, error="Invalid batch format", status_code=400)

        predictions = data["predictions"]

        if not isinstance(predictions, list) or len(predictions) == 0:
            return create_response(False, error="Predictions list is empty or invalid", status_code=400)

        if len(predictions) > 1000:
            return create_response(False, error="Batch size exceeds limit (max: 1000)", status_code=400)

        logger.info(f"Batch prediction request: {len(predictions)} samples")

        results = []
        for idx, pred_data in enumerate(predictions):
            try:
                success, input_scaled, error_msg = prepare_input(pred_data)

                if not success:
                    results.append({
                        "index": idx,
                        "success": False,
                        "error": error_msg
                    })
                    continue

                # Perform prediction
                failure_pred = failure_model.predict(input_scaled)[0]
                failure_proba = failure_model.predict_proba(input_scaled)[0]

                result = {
                    "index": idx,
                    "success": True,
                    "failure_predicted": int(failure_pred),
                    "failure_confidence": round(float(failure_proba[1]), 4),
                    "risk_level": get_risk_level(float(failure_proba[1]), failure_pred)
                }

                results.append(result)

            except Exception as e:
                logger.warning(f"Error processing batch item {idx}: {str(e)}")
                results.append({
                    "index": idx,
                    "success": False,
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"Batch prediction complete: {success_count}/{len(predictions)} successful")

        return create_response(True, data={
            "total": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "results": results
        })

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}", exc_info=True)
        return create_response(False, error=f"Batch prediction failed: {str(e)}", status_code=500)


@app.route("/info", methods=["GET"])
def info():
    """Get API and model information"""
    info_data = {
        "api_version": MODEL_VERSION,
        "models_loaded": model_loaded,
        "features": feature_columns if model_loaded else None,
        "valid_ranges": DataValidator.VALID_RANGES,
        "valid_types": DataValidator.VALID_TYPES,
        "fault_types": {
            "HDF": "Heat Dissipation Failure",
            "TWF": "Tool Wear Failure",
            "PWF": "Power Failure",
            "OSF": "Overstrain Failure",
            "RNF": "Random Component Failure"
        }
    }

    if model_loaded and model_metadata:
        info_data["model_metadata"] = model_metadata

    return jsonify(info_data)


def get_risk_level(confidence: float, prediction: int) -> str:
    """Determine risk level based on prediction and confidence"""
    if prediction == 0:
        return "LOW"
    elif confidence < 0.6:
        return "MEDIUM"
    elif confidence < 0.8:
        return "HIGH"
    else:
        return "CRITICAL"


def get_recommendations(prediction: int, confidence: float) -> list:
    """Get maintenance recommendations based on prediction"""
    recommendations = []

    if prediction == 0:
        recommendations.append("Machine operating normally")
        recommendations.append("Continue standard maintenance schedule")
    else:
        recommendations.append("Potential failure detected")
        if confidence > 0.8:
            recommendations.append("URGENT: Schedule immediate maintenance")
            recommendations.append("Reduce machine load or stop operation")
        elif confidence > 0.6:
            recommendations.append("Schedule maintenance within 24 hours")
            recommendations.append("Monitor machine parameters closely")
        else:
            recommendations.append("Monitor machine closely")
            recommendations.append("Schedule maintenance inspection")

    return recommendations


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors"""
    return create_response(False, error="Bad request", status_code=400)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return create_response(False, error="Endpoint not found", status_code=404)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return create_response(False, error="Internal server error", status_code=500)


if __name__ == "__main__":
    # Load models on startup
    if load_models():
        logger.info("Starting Predictive Maintenance API...")
        app.run(host="0.0.0.0", port=5001, debug=False)
    else:
        logger.error("Failed to load models. Exiting.")

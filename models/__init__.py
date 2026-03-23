"""CARVanta models package."""

try:
    from models.predict import predict_viability
except ImportError:
    # Model dependencies (joblib, numpy, sklearn) not available
    predict_viability = None

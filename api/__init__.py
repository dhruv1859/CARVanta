"""CARVanta API package."""

try:
    from api.main import app
except ImportError:
    # FastAPI not installed – API will be loaded via uvicorn directly
    app = None

import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
    SERVER_NAME_DISPLAY = os.environ.get("SERVER_NAME_DISPLAY", "MyServer")
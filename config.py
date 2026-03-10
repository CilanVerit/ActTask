import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://postgres:myacttask@localhost:5432/acttask"
        # "postgresql://postgres:myacttask@localhost:5432/acttask" - PostgreSQL version
        # "sqlite:///acttask.db" - SQLite version
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
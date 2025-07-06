from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the same directory as this file (backend/)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Read the database URI
DB_URI = os.getenv("DB_URI")

# Optional: raise an error if DB_URI is missing
if not DB_URI:
    raise ValueError("DB_URI not found in environment variables.")

# Create SQLAlchemy engine
engine = create_engine(DB_URI)
from dotenv import load_dotenv
import os

# Try loading .env from current directory
result = load_dotenv(dotenv_path=".env")

print("dotenv load result:", result)
print("DB_URI loaded:", os.getenv("DB_URI"))

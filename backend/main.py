from fastapi import FastAPI, Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from db import engine
from utils import get_schema_metadata, local_generate_sql

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"

# FastAPI setup
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider tightening this to localhost or your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key dependency
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

# Request body model
class QueryRequest(BaseModel):
    question: str

# Ask endpoint
@app.post("/ask")
async def ask_data(req: QueryRequest, _: str = Depends(verify_api_key)):
    try:
        schema = get_schema_metadata()
        sql = local_generate_sql(req.question, schema)
        print("Generated SQL:\n", sql)

        # If no valid SQL was generated
        if sql.strip().startswith("-- No matching SQL"):
            return {"message": sql.strip()}

        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row._mapping) for row in result]

        return {"result": rows}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

from transformers import pipeline
from db import engine
from sqlalchemy import text
from sql_templates import generate_sql_from_template  # ← add this

nlp = pipeline("text-generation", model="gpt2")  # still used as fallback

def local_generate_sql(question: str, schema: str) -> str:
    # Try template-based match first
    template_sql = generate_sql_from_template(question)
    if template_sql:
        return template_sql

    # If not matched, fallback to GPT-2
    prompt = f"""You are a helpful assistant that converts natural language to SQL.
Here is the database schema:

{schema}

Translate the following question into a correct MySQL SQL query.
Question: {question}
SQL:"""

    try:
        response = nlp(prompt, max_length=100, do_sample=False)[0]["generated_text"]

        if "SQL:" in response:
            sql_lines = response.split("SQL:")[-1].strip().split("\n")
            for line in sql_lines:
                if "select" in line.lower():
                    return line.strip()
    except Exception as e:
        print(f"LLM generation failed: {e}")

    return "SELECT * FROM orders LIMIT 10;"

def get_schema_metadata() -> str:
    """
    Fetches table and column metadata from the connected MySQL database.
    Returns a formatted string representation of the schema.
    """
    schema = ""
    with engine.connect() as conn:
        tables = conn.execute(text("SHOW TABLES")).fetchall()
        for (table_name,) in tables:
            schema += f"\nTable: {table_name}\n"
            columns = conn.execute(text(f"DESCRIBE {table_name}")).fetchall()
            for col in columns:
                schema += f"  - {col[0]} ({col[1]})\n"
    return schema


# AI Assisted Dashboard (Local Testing)

## Description

Ask natural language questions to query your MySQL database using GPT-4.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your-key-here  # Windows: set OPENAI_API_KEY=your-key-here
```

3. Start the backend:

```bash
cd backend
uvicorn main:app --reload
```

4. In a new terminal, start the frontend:

```bash
cd frontend
streamlit run app.py
```

5. Open browser at `http://localhost:8501`

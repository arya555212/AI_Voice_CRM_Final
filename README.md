# AI Voice CRM

FastAPI + SQLite CRM with contacts, leads, local Ollama assistant, call history empty state, and Telnyx-ready display placeholders.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Default demo login: `admin` / `admin123` (change before production).

## Ollama
Set `OLLAMA_URL` and `OLLAMA_MODEL` from `.env.example`. Default model is `gemma4:2b`.

# Local Development Setup

## Backend

```bash
cd backend
pip install -r requirements.txt --break-system-packages
pytest -v
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`.

## Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

This starts the backend, frontend, and DynamoDB Local. Amazon Bedrock is
not started locally — it remains an external AWS dependency (see
`.env.example`, `BEDROCK_MODEL_ID`).

## Running tests

```bash
make backend-test
```

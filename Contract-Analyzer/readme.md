
# Layer 3 — Async Task Queue

> Part of the **Contract Analyzer** project. This layer handles asynchronous job processing so the app never blocks waiting for heavy AI tasks.

---

## What's Running

| Service | Role |
|---------|------|
| **Flask** | Accepts uploads, returns a Task ID instantly |
| **Redis** | Queues jobs, stores results |
| **Celery** | Background worker that processes the job |

---

## Run It

```bash
docker compose up --build
```

**Upload a job**
```
POST http://localhost:5000/upload
{"filename": "my_contract.pdf"}
```

**Poll for result**
```
GET http://localhost:5000/status/<task_id>
```

---

## Structure

```
contract-analyzer/
├── docker-compose.yml
├── flask_app/
│   ├── app.py          # /upload and /status routes
│   └── ...
└── celery_worker/
    ├── tasks.py        # process_document task (dummy for now)
    └── ...
```

---

> `tasks.py` currently uses dummy data. It gets replaced with real logic in Layers 4–7.

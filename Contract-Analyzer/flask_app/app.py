from flask import Flask, request, jsonify
from celery import Celery
import os

app = Flask(__name__)

# --- Celery Configuration ---
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery(app.name, broker=BROKER_URL, backend=RESULT_BACKEND)


# --- Routes ---

@app.route("/upload", methods=["POST"])
def upload():
    """
    Accepts a file upload (or dummy JSON for now).
    Immediately returns a Task ID without waiting for processing.
    """
    # For now we send a dummy payload — later this will be the actual PDF content
    filename = request.json.get("filename", "test_contract.pdf")

    # Fire the Celery task asynchronously
    task = celery.send_task("tasks.process_document", args=[filename])

    return jsonify({
        "message": "File received. Processing started.",
        "task_id": task.id
    }), 202


@app.route("/status/<task_id>", methods=["GET"])
def status(task_id):
    """
    Poll this endpoint with the Task ID to check processing status.
    """
    task = celery.AsyncResult(task_id)

    if task.state == "PENDING":
        response = {"status": "PENDING", "message": "Task is waiting in queue..."}
    elif task.state == "STARTED":
        response = {"status": "STARTED", "message": "Task is currently being processed..."}
    elif task.state == "SUCCESS":
        response = {"status": "SUCCESS", "result": task.result}
    elif task.state == "FAILURE":
        response = {"status": "FAILURE", "message": str(task.info)}
    else:
        response = {"status": task.state}

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
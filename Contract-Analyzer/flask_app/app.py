from flask import Flask, request, jsonify
from celery import Celery
import os

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery(app.name, broker=BROKER_URL, backend=RESULT_BACKEND)

UPLOAD_FOLDER = "/uploads"


@app.route("/upload", methods=["POST"])
def upload():
    # Check a file was actually sent
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files accepted"}), 400

    # Save the PDF to the shared uploads folder
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Fire the Celery task with the saved filepath
    task = celery.send_task("tasks.process_document", args=[filepath])

    return jsonify({
        "message": "File received. Processing started.",
        "task_id": task.id,
        "filename": file.filename
    }), 202


@app.route("/status/<task_id>", methods=["GET"])
def status(task_id):
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
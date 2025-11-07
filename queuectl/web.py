# Web frontend for QueueCTL using Flask
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from .storage import JobStorage
from .models import Job, JobState
from .worker import WorkerManager
from .config import Config

# Get the directory where this module is located
module_dir = Path(__file__).parent
template_dir = module_dir / 'templates'
static_dir = module_dir / 'static'

app = Flask(__name__, 
            template_folder=str(template_dir),
            static_folder=str(static_dir))
CORS(app)

# Global instances
storage = JobStorage()
app_config = Config()
worker_manager = WorkerManager(storage, app_config)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    all_jobs = storage.get_all_jobs()
    
    counts = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
        "dead": 0
    }
    
    for job in all_jobs:
        counts[job.state.value] = counts.get(job.state.value, 0) + 1
    
    return jsonify({
        "total_jobs": len(all_jobs),
        "pending": counts['pending'],
        "processing": counts['processing'],
        "completed": counts['completed'],
        "failed": counts['failed'],
        "dead": counts['dead'],
        "active_workers": worker_manager.get_active_worker_count()
    })


@app.route('/api/jobs')
def get_jobs():
    state = request.args.get('state')
    
    if state:
        try:
            state_enum = JobState(state)
            jobs = storage.get_jobs_by_state(state_enum)
        except ValueError:
            jobs = storage.get_all_jobs()
    else:
        jobs = storage.get_all_jobs()
    
    # Sort by created_at
    jobs.sort(key=lambda j: j.created_at)
    
    return jsonify([job.to_dict() for job in jobs])


@app.route('/api/jobs', methods=['POST'])
def enqueue_job():
    data = request.json
    
    if not data or 'id' not in data or 'command' not in data:
        return jsonify({"error": "Job must have 'id' and 'command' fields"}), 400
    
    # Check if job already exists
    existing_job = storage.get_job(data['id'])
    if existing_job:
        return jsonify({"error": f"Job with id '{data['id']}' already exists"}), 400
    
    # Create job
    job = Job(
        job_id=data['id'],
        command=data['command'],
        max_retries=data.get('max_retries', app_config.get('max_retries', 3))
    )
    
    storage.save_job(job)
    return jsonify(job.to_dict()), 201


@app.route('/api/jobs/<job_id>')
def get_job(job_id):
    job = storage.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job.to_dict())


@app.route('/api/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    job = storage.get_job(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    if job.state != JobState.DEAD:
        return jsonify({"error": "Job is not in Dead Letter Queue"}), 400
    
    # Reset job to pending state
    job.state = JobState.PENDING
    job.attempts = 0
    job.error_message = None
    job.next_retry_at = None
    job.updated_at = job._now()
    
    storage.save_job(job)
    return jsonify(job.to_dict())


@app.route('/api/dlq')
def get_dlq():
    dead_jobs = storage.get_dead_jobs()
    return jsonify([job.to_dict() for job in dead_jobs])


@app.route('/api/config')
def get_config():
    all_config = app_config.get_all()
    return jsonify(all_config)


@app.route('/api/config', methods=['POST'])
def set_config():
    data = request.json
    
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({"error": "Must provide 'key' and 'value'"}), 400
    
    key = data['key']
    value = data['value']
    
    # Convert key from kebab-case to snake_case
    key_map = {
        "max-retries": "max_retries",
        "backoff-base": "backoff_base",
        "worker-poll-interval": "worker_poll_interval",
        "job-timeout": "job_timeout"
    }
    
    internal_key = key_map.get(key, key)
    
    # Convert value to appropriate type
    try:
        if internal_key in ["max_retries", "job_timeout"]:
            value = int(value)
        elif internal_key in ["backoff_base", "worker_poll_interval"]:
            value = float(value)
    except ValueError:
        return jsonify({"error": f"Invalid value type for '{key}'"}), 400
    
    try:
        app_config.set(internal_key, value)
        return jsonify({"success": True, "key": key, "value": value})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/workers/start', methods=['POST'])
def start_workers():
    data = request.json or {}
    count = data.get('count', 1)
    
    if count < 1:
        return jsonify({"error": "Worker count must be at least 1"}), 400
    
    if worker_manager.running:
        return jsonify({"error": "Workers are already running"}), 400
    
    try:
        worker_manager.start_workers(count)
        return jsonify({"success": True, "message": f"Started {count} worker(s)", "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/workers/stop', methods=['POST'])
def stop_workers():
    if not worker_manager.running:
        return jsonify({"error": "No workers are running"}), 400
    
    try:
        worker_manager.stop_workers()
        return jsonify({"success": True, "message": "All workers stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/workers/status')
def get_workers_status():
    return jsonify({
        "running": worker_manager.running,
        "active_count": worker_manager.get_active_worker_count(),
        "total_workers": len(worker_manager.workers)
    })


@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = storage.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    success = storage.delete_job(job_id)
    if success:
        return jsonify({"success": True, "message": f"Job '{job_id}' deleted"})
    else:
        return jsonify({"error": "Failed to delete job"}), 500


def run_web_server(host='127.0.0.1', port=5000, debug=False):
    app.run(host=host, port=port, debug=debug)


import json
import sys
import click
from .storage import JobStorage
from .models import Job, JobState
from .worker import WorkerManager
from .config import Config

storage = JobStorage()
app_config = Config()
worker_manager = WorkerManager(storage, app_config)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    pass


@cli.command()
@click.argument('job_data', type=str)
def enqueue(job_data):
    try:
        job_dict = json.loads(job_data)
        
        if "id" not in job_dict or "command" not in job_dict:
            click.echo("Error: Job must have 'id' and 'command' fields", err=True)
            sys.exit(1)
        
        existing_job = storage.get_job(job_dict["id"])
        if existing_job:
            click.echo(f"Error: Job with id '{job_dict['id']}' already exists", err=True)
            sys.exit(1)
        
        job = Job(
            job_id=job_dict["id"],
            command=job_dict["command"],
            max_retries=job_dict.get("max_retries", app_config.get("max_retries", 3)),
            priority=job_dict.get("priority", 5),
            run_at=job_dict.get("run_at")
        )
        
        storage.save_job(job)
        click.echo(f"Job '{job.id}' enqueued successfully")
    
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON format", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def worker():
    """Manage worker processes"""
    pass


@worker.command()
@click.option('--count', default=1, type=int, help='Number of workers to start')
def start(count):
    if count < 1:
        click.echo("Error: Worker count must be at least 1", err=True)
        sys.exit(1)
    
    worker_manager.start_workers(count)
    
    try:
        while worker_manager.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        worker_manager.stop_workers()


@worker.command()
def stop():
    worker_manager.stop_workers()


@cli.command()
def status():
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
    
    click.echo("=== Queue Status ===")
    click.echo(f"Total Jobs: {len(all_jobs)}")
    click.echo(f"Pending: {counts['pending']}")
    click.echo(f"Processing: {counts['processing']}")
    click.echo(f"Completed: {counts['completed']}")
    click.echo(f"Failed: {counts['failed']}")
    click.echo(f"Dead (DLQ): {counts['dead']}")
    click.echo(f"Active Workers: {worker_manager.get_active_worker_count()}")


@cli.command()
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed', 'dead']), 
              help='Filter jobs by state')
def list(state):
    if state:
        state_enum = JobState(state)
        jobs = storage.get_jobs_by_state(state_enum)
    else:
        jobs = storage.get_all_jobs()
    
    if not jobs:
        click.echo("No jobs found")
        return
    
    jobs.sort(key=lambda j: j.created_at)
    
    click.echo(f"\n{'ID':<20} {'State':<12} {'Attempts':<10} {'Command':<40}")
    click.echo("-" * 82)
    
    for job in jobs:
        command_preview = job.command[:37] + "..." if len(job.command) > 40 else job.command
        click.echo(f"{job.id:<20} {job.state.value:<12} {job.attempts}/{job.max_retries:<9} {command_preview:<40}")


@cli.group()
def dlq():
    pass


@dlq.command()
def list():
    dead_jobs = storage.get_dead_jobs()
    
    if not dead_jobs:
        click.echo("No jobs in Dead Letter Queue")
        return
    
    click.echo(f"\nDead Letter Queue ({len(dead_jobs)} jobs):")
    click.echo("-" * 80)
    
    for job in dead_jobs:
        click.echo(f"\nJob ID: {job.id}")
        click.echo(f"  Command: {job.command}")
        click.echo(f"  Attempts: {job.attempts}/{job.max_retries}")
        click.echo(f"  Failed At: {job.updated_at}")
        if job.error_message:
            click.echo(f"  Error: {job.error_message}")


@dlq.command()
@click.argument('job_id', type=str)
def retry(job_id):
    job = storage.get_job(job_id)
    
    if not job:
        click.echo(f"Error: Job '{job_id}' not found", err=True)
        sys.exit(1)
    
    if job.state != JobState.DEAD:
        click.echo(f"Error: Job '{job_id}' is not in Dead Letter Queue", err=True)
        sys.exit(1)
    
    job.state = JobState.PENDING
    job.attempts = 0
    job.error_message = None
    job.next_retry_at = None
    job.updated_at = job._now()
    
    storage.save_job(job)
    click.echo(f"Job '{job_id}' moved back to queue for retry")


@cli.group()
def config():
    pass


@config.command()
@click.argument('key', type=str)
@click.argument('value', type=str)
def set(key, value):
    key_map = {
        "max-retries": "max_retries",
        "backoff-base": "backoff_base",
        "worker-poll-interval": "worker_poll_interval",
        "job-timeout": "job_timeout"
    }
    
    internal_key = key_map.get(key, key)
    
    try:
        if internal_key in ["max_retries", "job_timeout"]:
            value = int(value)
        elif internal_key in ["backoff_base", "worker_poll_interval"]:
            value = float(value)
    except ValueError:
        click.echo(f"Error: Invalid value type for '{key}'", err=True)
        sys.exit(1)
    
    try:
        app_config.set(internal_key, value)
        click.echo(f"Configuration '{key}' set to {value}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command()
def show():
    all_config = app_config.get_all()
    click.echo("Current Configuration:")
    click.echo("-" * 40)
    
    key_map = {
        "max_retries": "max-retries",
        "backoff_base": "backoff-base",
        "worker_poll_interval": "worker-poll-interval",
        "job_timeout": "job-timeout"
    }
    
    for key, value in all_config.items():
        display_key = key_map.get(key, key)
        click.echo(f"{display_key}: {value}")


@cli.group()
def job():
    """Job management commands"""
    pass


@job.command()
@click.argument('job_id', type=str)
@click.option('--stdout', is_flag=True, help='Show stdout only')
@click.option('--stderr', is_flag=True, help='Show stderr only')
def output(job_id, stdout, stderr):
    """View job output (stdout/stderr)"""
    job = storage.get_job(job_id)
    if not job:
        click.echo(f"Error: Job '{job_id}' not found", err=True)
        sys.exit(1)
    
    if stdout and stderr:
        click.echo("Error: Cannot use --stdout and --stderr together", err=True)
        sys.exit(1)
    
    if stdout:
        if job.stdout:
            click.echo(job.stdout)
        else:
            click.echo("(no stdout output)")
    elif stderr:
        if job.stderr:
            click.echo(job.stderr)
        else:
            click.echo("(no stderr output)")
    else:
        if job.stdout:
            click.echo("=== STDOUT ===")
            click.echo(job.stdout)
        if job.stderr:
            if job.stdout:
                click.echo("\n=== STDERR ===")
            click.echo(job.stderr)
        if not job.stdout and not job.stderr:
            click.echo("(no output available)")


@cli.command()
def metrics():
    """Show execution metrics and statistics"""
    all_jobs = storage.get_all_jobs()
    
    completed_jobs = [j for j in all_jobs if j.state == JobState.COMPLETED]
    failed_jobs = [j for j in all_jobs if j.state == JobState.FAILED]
    dead_jobs = [j for j in all_jobs if j.state == JobState.DEAD]
    
    total_jobs = len(all_jobs)
    total_completed = len(completed_jobs)
    total_failed = len(failed_jobs)
    total_dead = len(dead_jobs)
    
    processed_jobs = total_completed + total_failed + total_dead
    success_rate = (total_completed / processed_jobs * 100) if processed_jobs > 0 else 0
    
    jobs_with_time = [j for j in completed_jobs if j.execution_time is not None]
    avg_execution_time = sum(j.execution_time for j in jobs_with_time) / len(jobs_with_time) if jobs_with_time else 0
    
    total_execution_time = sum(j.execution_time for j in jobs_with_time if j.execution_time)
    
    fastest_job = min(jobs_with_time, key=lambda j: j.execution_time) if jobs_with_time else None
    slowest_job = max(jobs_with_time, key=lambda j: j.execution_time) if jobs_with_time else None
    
    click.echo("=== Execution Metrics ===")
    click.echo(f"Total Jobs: {total_jobs}")
    click.echo(f"Completed: {total_completed}")
    click.echo(f"Failed: {total_failed}")
    click.echo(f"Dead (DLQ): {total_dead}")
    click.echo(f"Success Rate: {success_rate:.2f}%")
    click.echo("")
    click.echo("=== Execution Time Statistics ===")
    if jobs_with_time:
        click.echo(f"Average Execution Time: {avg_execution_time:.3f}s")
        click.echo(f"Total Execution Time: {total_execution_time:.3f}s")
        if fastest_job:
            click.echo(f"Fastest Job: {fastest_job.id} ({fastest_job.execution_time:.3f}s)")
        if slowest_job:
            click.echo(f"Slowest Job: {slowest_job.id} ({slowest_job.execution_time:.3f}s)")
    else:
        click.echo("No execution time data available")


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, type=int, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def web(host, port, debug):
    try:
        from .web import run_web_server
        click.echo(f"Starting web server on http://{host}:{port}")
        click.echo("Press Ctrl+C to stop")
        run_web_server(host=host, port=port, debug=debug)
    except ImportError:
        click.echo("Error: Flask is not installed. Run: pip install flask flask-cors", err=True)
        sys.exit(1)


def main():
    cli()


if __name__ == "__main__":
    main()

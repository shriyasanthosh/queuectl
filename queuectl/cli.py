"""
CLI interface for QueueCTL
"""
import json
import sys
import click
from .storage import JobStorage
from .models import Job, JobState
from .worker import WorkerManager
from .config import Config


# Global instances
storage = JobStorage()
config = Config()
worker_manager = WorkerManager(storage, config)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """QueueCTL - CLI-based background job queue system"""
    pass


@cli.command()
@click.argument('job_data', type=str)
def enqueue(job_data):
    """Enqueue a new job to the queue
    
    JOB_DATA: JSON string with job details (id, command, max_retries optional)
    
    Example: queuectl enqueue '{"id":"job1","command":"echo hello"}'
    """
    try:
        job_dict = json.loads(job_data)
        
        # Validate required fields
        if "id" not in job_dict or "command" not in job_dict:
            click.echo("Error: Job must have 'id' and 'command' fields", err=True)
            sys.exit(1)
        
        # Check if job already exists
        existing_job = storage.get_job(job_dict["id"])
        if existing_job:
            click.echo(f"Error: Job with id '{job_dict['id']}' already exists", err=True)
            sys.exit(1)
        
        # Create job
        job = Job(
            job_id=job_dict["id"],
            command=job_dict["command"],
            max_retries=job_dict.get("max_retries", config.get("max_retries", 3))
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
    """Start worker processes"""
    if count < 1:
        click.echo("Error: Worker count must be at least 1", err=True)
        sys.exit(1)
    
    worker_manager.start_workers(count)
    
    # Keep the process running
    try:
        while worker_manager.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        worker_manager.stop_workers()


@worker.command()
def stop():
    """Stop all running workers gracefully"""
    worker_manager.stop_workers()


@cli.command()
def status():
    """Show summary of all job states and active workers"""
    all_jobs = storage.get_all_jobs()
    
    # Count jobs by state
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
    """List jobs, optionally filtered by state"""
    if state:
        state_enum = JobState(state)
        jobs = storage.get_jobs_by_state(state_enum)
    else:
        jobs = storage.get_all_jobs()
    
    if not jobs:
        click.echo("No jobs found")
        return
    
    # Sort by created_at
    jobs.sort(key=lambda j: j.created_at)
    
    click.echo(f"\n{'ID':<20} {'State':<12} {'Attempts':<10} {'Command':<40}")
    click.echo("-" * 82)
    
    for job in jobs:
        command_preview = job.command[:37] + "..." if len(job.command) > 40 else job.command
        click.echo(f"{job.id:<20} {job.state.value:<12} {job.attempts}/{job.max_retries:<9} {command_preview:<40}")


@cli.group()
def dlq():
    """Manage Dead Letter Queue"""
    pass


@dlq.command()
def list():
    """List all jobs in the Dead Letter Queue"""
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
    """Retry a job from the Dead Letter Queue"""
    job = storage.get_job(job_id)
    
    if not job:
        click.echo(f"Error: Job '{job_id}' not found", err=True)
        sys.exit(1)
    
    if job.state != JobState.DEAD:
        click.echo(f"Error: Job '{job_id}' is not in Dead Letter Queue", err=True)
        sys.exit(1)
    
    # Reset job to pending state
    job.state = JobState.PENDING
    job.attempts = 0
    job.error_message = None
    job.next_retry_at = None
    job.updated_at = job._now()
    
    storage.save_job(job)
    click.echo(f"Job '{job_id}' moved back to queue for retry")


@cli.group()
def config():
    """Manage configuration"""
    pass


@config.command()
@click.argument('key', type=str)
@click.argument('value', type=str)
def set(key, value):
    """Set a configuration value
    
    Keys: max-retries, backoff-base, worker-poll-interval, job-timeout
    """
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
        click.echo(f"Error: Invalid value type for '{key}'", err=True)
        sys.exit(1)
    
    try:
        config.set(internal_key, value)
        click.echo(f"Configuration '{key}' set to {value}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command()
def show():
    """Show current configuration"""
    all_config = config.get_all()
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


def main():
    """Entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()


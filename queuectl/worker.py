"""
Worker process management
"""
import os
import signal
import sys
import time
import threading
from pathlib import Path
from typing import Optional
from .storage import JobStorage
from .models import Job, JobState
from .executor import JobExecutor
from .config import Config
from datetime import datetime, timedelta


class Worker:
    """Worker process that processes jobs from the queue"""
    
    def __init__(self, worker_id: int, storage: JobStorage, config: Config):
        self.worker_id = worker_id
        self.storage = storage
        self.config = config
        self.executor = JobExecutor(config)
        self.running = False
        self.current_job: Optional[Job] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the worker"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._work_loop, daemon=False)
        self.thread.start()
    
    def stop(self):
        """Stop the worker gracefully"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
    
    def _work_loop(self):
        """Main worker loop"""
        poll_interval = self.config.get("worker_poll_interval", 1.0)
        backoff_base = self.config.get("backoff_base", 2.0)
        
        while self.running:
            try:
                # Try to get a pending job
                job = self._get_next_job()
                
                if job:
                    self._process_job(job, backoff_base)
                else:
                    # No jobs available, wait before checking again
                    time.sleep(poll_interval)
            
            except Exception as e:
                # Log error and continue
                print(f"Worker {self.worker_id} error: {e}", file=sys.stderr)
                time.sleep(poll_interval)
    
    def _get_next_job(self) -> Optional[Job]:
        """Get the next job to process (with locking)"""
        # Try pending jobs first
        pending_jobs = self.storage.get_pending_jobs()
        if pending_jobs:
            job = pending_jobs[0]
            # Try to claim it by marking as processing
            if self._claim_job(job):
                return job
        
        # Try failed jobs that are ready for retry
        failed_jobs = self.storage.get_failed_jobs()
        if failed_jobs:
            job = failed_jobs[0]
            if self._claim_job(job):
                return job
        
        return None
    
    def _claim_job(self, job: Job) -> bool:
        """Try to claim a job by marking it as processing"""
        # Reload job to ensure we have latest state
        current_job = self.storage.get_job(job.id)
        if not current_job or current_job.state != job.state:
            return False
        
        # Mark as processing
        current_job.mark_processing()
        self.storage.save_job(current_job)
        return True
    
    def _process_job(self, job: Job, backoff_base: float):
        """Process a single job"""
        self.current_job = job
        
        try:
            # Execute the job
            success, error_message = self.executor.execute(job)
            
            if success:
                # Job completed successfully
                job.mark_completed()
                self.storage.save_job(job)
            else:
                # Job failed
                job.mark_failed(error_message)
                
                if job.should_retry():
                    # Calculate retry delay
                    delay = job.calculate_retry_delay(backoff_base)
                    next_retry = datetime.utcnow() + timedelta(seconds=delay)
                    job.next_retry_at = next_retry.isoformat() + "Z"
                    job.state = JobState.FAILED
                    self.storage.save_job(job)
                else:
                    # Max retries exceeded, move to DLQ
                    job.mark_dead(f"Max retries ({job.max_retries}) exceeded. Last error: {error_message}")
                    self.storage.save_job(job)
        
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error: {str(e)}"
            job.mark_failed(error_msg)
            
            if job.should_retry():
                delay = job.calculate_retry_delay(backoff_base)
                next_retry = datetime.utcnow() + timedelta(seconds=delay)
                job.next_retry_at = next_retry.isoformat() + "Z"
                job.state = JobState.FAILED
                self.storage.save_job(job)
            else:
                job.mark_dead(error_msg)
                self.storage.save_job(job)
        
        finally:
            self.current_job = None


class WorkerManager:
    """Manages multiple worker processes"""
    
    def __init__(self, storage: JobStorage, config: Config, pid_file: str = "worker.pid"):
        self.storage = storage
        self.config = config
        self.pid_file = Path(pid_file)
        self.workers: list[Worker] = []
        self.running = False
    
    def start_workers(self, count: int):
        """Start multiple workers"""
        if self.running:
            print("Workers are already running")
            return
        
        self.running = True
        
        # Create and start workers
        for i in range(count):
            worker = Worker(i + 1, self.storage, self.config)
            worker.start()
            self.workers.append(worker)
        
        # Save PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        print(f"Started {count} worker(s)")
    
    def stop_workers(self):
        """Stop all workers gracefully"""
        if not self.running:
            print("No workers are running")
            return
        
        print("Stopping workers gracefully...")
        self.running = False
        
        # Wait for current jobs to finish
        max_wait = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            all_idle = all(w.current_job is None for w in self.workers)
            if all_idle:
                break
            time.sleep(0.5)
        
        # Stop all workers
        for worker in self.workers:
            worker.stop()
        
        self.workers.clear()
        
        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()
        
        print("All workers stopped")
    
    def get_active_worker_count(self) -> int:
        """Get number of active workers"""
        return len([w for w in self.workers if w.running])


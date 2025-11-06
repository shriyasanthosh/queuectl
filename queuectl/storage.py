"""
Persistent storage for jobs using JSON file
"""
import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .models import Job, JobState


class JobStorage:
    """Thread-safe persistent storage for jobs"""
    
    def __init__(self, storage_path: str = "jobs.json"):
        self.storage_path = Path(storage_path)
        self.lock = threading.Lock()
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Create storage file if it doesn't exist"""
        if not self.storage_path.exists():
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)
    
    def _load_jobs(self) -> Dict[str, dict]:
        """Load all jobs from storage"""
        with self.lock:
            try:
                if not self.storage_path.exists():
                    return {}
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except (json.JSONDecodeError, IOError):
                return {}
    
    def _save_jobs(self, jobs: Dict[str, dict]):
        """Save all jobs to storage"""
        with self.lock:
            try:
                with open(self.storage_path, 'w') as f:
                    json.dump(jobs, f, indent=2)
            except IOError as e:
                raise RuntimeError(f"Failed to save jobs: {e}")
    
    def save_job(self, job: Job):
        """Save or update a job"""
        jobs = self._load_jobs()
        jobs[job.id] = job.to_dict()
        self._save_jobs(jobs)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        jobs = self._load_jobs()
        job_data = jobs.get(job_id)
        if job_data:
            return Job.from_dict(job_data)
        return None
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        jobs = self._load_jobs()
        return [Job.from_dict(job_data) for job_data in jobs.values()]
    
    def get_jobs_by_state(self, state: JobState) -> List[Job]:
        """Get all jobs with a specific state"""
        all_jobs = self.get_all_jobs()
        return [job for job in all_jobs if job.state == state]
    
    def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs"""
        return self.get_jobs_by_state(JobState.PENDING)
    
    def get_failed_jobs(self) -> List[Job]:
        """Get all failed jobs ready for retry"""
        all_jobs = self.get_all_jobs()
        now = datetime.utcnow()
        failed_jobs = []
        
        for job in all_jobs:
            if job.state == JobState.FAILED and job.should_retry():
                # Check if retry delay has passed
                if job.next_retry_at:
                    try:
                        retry_time = datetime.fromisoformat(job.next_retry_at.replace('Z', '+00:00'))
                        if retry_time <= now:
                            failed_jobs.append(job)
                    except (ValueError, AttributeError):
                        # If parsing fails, include the job
                        failed_jobs.append(job)
                else:
                    failed_jobs.append(job)
        
        return failed_jobs
    
    def get_dead_jobs(self) -> List[Job]:
        """Get all dead jobs (DLQ)"""
        return self.get_jobs_by_state(JobState.DEAD)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        jobs = self._load_jobs()
        if job_id in jobs:
            del jobs[job_id]
            self._save_jobs(jobs)
            return True
        return False
    
    def clear_all(self):
        """Clear all jobs (use with caution)"""
        self._save_jobs({})


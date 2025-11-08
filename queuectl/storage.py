import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from .models import Job, JobState


class JobStorage:
    
    def __init__(self, storage_path: str = "jobs.json"):
        self.storage_path = Path(storage_path)
        self.lock = threading.Lock()
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        if not self.storage_path.exists():
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)
    
    def _load_jobs(self) -> Dict[str, dict]:
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
        with self.lock:
            try:
                with open(self.storage_path, 'w') as f:
                    json.dump(jobs, f, indent=2)
            except IOError as e:
                raise RuntimeError(f"Failed to save jobs: {e}")
    
    def save_job(self, job: Job):
        jobs = self._load_jobs()
        jobs[job.id] = job.to_dict()
        self._save_jobs(jobs)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        jobs = self._load_jobs()
        job_data = jobs.get(job_id)
        if job_data:
            return Job.from_dict(job_data)
        return None
    
    def get_all_jobs(self) -> List[Job]:
        jobs = self._load_jobs()
        return [Job.from_dict(job_data) for job_data in jobs.values()]
    
    def get_jobs_by_state(self, state: JobState) -> List[Job]:
        all_jobs = self.get_all_jobs()
        return [job for job in all_jobs if job.state == state]
    
    def get_pending_jobs(self) -> List[Job]:
        all_jobs = self.get_jobs_by_state(JobState.PENDING)
        now = datetime.now(timezone.utc)
        ready_jobs = []
        
        for job in all_jobs:
            if job.run_at:
                try:
                    run_time = datetime.fromisoformat(job.run_at.replace('Z', '+00:00'))
                    if run_time.tzinfo is None:
                        run_time = run_time.replace(tzinfo=timezone.utc)
                    if run_time > now:
                        continue
                except (ValueError, AttributeError):
                    pass
            
            ready_jobs.append(job)
        
        ready_jobs.sort(key=lambda j: (-j.priority, j.created_at))
        return ready_jobs
    
    def get_failed_jobs(self) -> List[Job]:
        all_jobs = self.get_all_jobs()
        now = datetime.now(timezone.utc)
        failed_jobs = []
        
        for job in all_jobs:
            if job.state == JobState.FAILED and job.should_retry():
                if job.next_retry_at:
                    try:
                        retry_time = datetime.fromisoformat(job.next_retry_at.replace('Z', '+00:00'))
                        if retry_time.tzinfo is None:
                            retry_time = retry_time.replace(tzinfo=timezone.utc)
                        if retry_time <= now:
                            failed_jobs.append(job)
                    except (ValueError, AttributeError):
                        failed_jobs.append(job)
                else:
                    failed_jobs.append(job)
        
        return failed_jobs
    
    def get_dead_jobs(self) -> List[Job]:
        return self.get_jobs_by_state(JobState.DEAD)
    
    def delete_job(self, job_id: str) -> bool:
        jobs = self._load_jobs()
        if job_id in jobs:
            del jobs[job_id]
            self._save_jobs(jobs)
            return True
        return False
    
    def clear_all(self):
        self._save_jobs({})

import json
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class JobState(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


class Job:
    
    def __init__(
        self,
        job_id: str,
        command: str,
        state: JobState = JobState.PENDING,
        attempts: int = 0,
        max_retries: int = 3,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        next_retry_at: Optional[str] = None,
        error_message: Optional[str] = None,
        priority: int = 5,
        run_at: Optional[str] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        execution_time: Optional[float] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None
    ):
        self.id = job_id
        self.command = command
        self.state = state
        self.attempts = attempts
        self.max_retries = max_retries
        self.created_at = created_at or self._now()
        self.updated_at = updated_at or self._now()
        self.next_retry_at = next_retry_at
        self.error_message = error_message
        self.priority = priority
        self.run_at = run_at
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.started_at = started_at
        self.completed_at = completed_at
    
    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "state": self.state.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "next_retry_at": self.next_retry_at,
            "error_message": self.error_message,
            "priority": self.priority,
            "run_at": self.run_at,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time": self.execution_time,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        return cls(
            job_id=data["id"],
            command=data["command"],
            state=JobState(data["state"]),
            attempts=data.get("attempts", 0),
            max_retries=data.get("max_retries", 3),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            next_retry_at=data.get("next_retry_at"),
            error_message=data.get("error_message"),
            priority=data.get("priority", 5),
            run_at=data.get("run_at"),
            stdout=data.get("stdout"),
            stderr=data.get("stderr"),
            execution_time=data.get("execution_time"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at")
        )
    
    def mark_processing(self):
        self.state = JobState.PROCESSING
        self.updated_at = self._now()
        self.started_at = self._now()
    
    def mark_completed(self):
        self.state = JobState.COMPLETED
        self.updated_at = self._now()
        self.completed_at = self._now()
        self.error_message = None
    
    def mark_failed(self, error_message: str = None):
        self.state = JobState.FAILED
        self.attempts += 1
        self.updated_at = self._now()
        self.error_message = error_message
    
    def mark_dead(self, error_message: str = None):
        self.state = JobState.DEAD
        self.updated_at = self._now()
        self.error_message = error_message
    
    def should_retry(self) -> bool:
        return self.attempts < self.max_retries and self.state == JobState.FAILED
    
    def calculate_retry_delay(self, base: float = 2.0) -> float:
        return base ** self.attempts

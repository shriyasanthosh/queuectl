"""
Job data models and state management
"""
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class JobState(Enum):
    """Job state enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


class Job:
    """Represents a single job in the queue"""
    
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
        error_message: Optional[str] = None
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
    
    @staticmethod
    def _now() -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "id": self.id,
            "command": self.command,
            "state": self.state.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "next_retry_at": self.next_retry_at,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create job from dictionary"""
        return cls(
            job_id=data["id"],
            command=data["command"],
            state=JobState(data["state"]),
            attempts=data.get("attempts", 0),
            max_retries=data.get("max_retries", 3),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            next_retry_at=data.get("next_retry_at"),
            error_message=data.get("error_message")
        )
    
    def mark_processing(self):
        """Mark job as being processed"""
        self.state = JobState.PROCESSING
        self.updated_at = self._now()
    
    def mark_completed(self):
        """Mark job as completed"""
        self.state = JobState.COMPLETED
        self.updated_at = self._now()
        self.error_message = None
    
    def mark_failed(self, error_message: str = None):
        """Mark job as failed"""
        self.state = JobState.FAILED
        self.attempts += 1
        self.updated_at = self._now()
        self.error_message = error_message
    
    def mark_dead(self, error_message: str = None):
        """Mark job as dead (moved to DLQ)"""
        self.state = JobState.DEAD
        self.updated_at = self._now()
        self.error_message = error_message
    
    def should_retry(self) -> bool:
        """Check if job should be retried"""
        return self.attempts < self.max_retries and self.state == JobState.FAILED
    
    def calculate_retry_delay(self, base: float = 2.0) -> float:
        """Calculate exponential backoff delay in seconds"""
        return base ** self.attempts


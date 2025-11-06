"""
Job execution logic
"""
import subprocess
import time
from typing import Tuple, Optional
from .models import Job
from .config import Config


class JobExecutor:
    """Executes jobs and handles timeouts"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def execute(self, job: Job) -> Tuple[bool, Optional[str]]:
        """
        Execute a job command
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Execute the command
            timeout = self.config.get("job_timeout", 300)
            
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return True, None
            else:
                error_msg = result.stderr or result.stdout or f"Command failed with exit code {result.returncode}"
                return False, error_msg.strip()
        
        except subprocess.TimeoutExpired:
            return False, f"Job timed out after {timeout} seconds"
        
        except FileNotFoundError:
            return False, "Command not found"
        
        except Exception as e:
            return False, f"Execution error: {str(e)}"


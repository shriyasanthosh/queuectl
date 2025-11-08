import subprocess
import time
from typing import Tuple, Optional, Dict, Any
from .models import Job
from .config import Config


class JobExecutor:
    
    def __init__(self, config: Config):
        self.config = config
    
    def execute(self, job: Job) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        start_time = time.time()
        execution_data = {
            "stdout": None,
            "stderr": None,
            "execution_time": None
        }
        
        try:
            timeout = self.config.get("job_timeout", 300)
            
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            execution_data["execution_time"] = execution_time
            execution_data["stdout"] = result.stdout
            execution_data["stderr"] = result.stderr
            
            if result.returncode == 0:
                return True, None, execution_data
            else:
                error_msg = result.stderr or result.stdout or f"Command failed with exit code {result.returncode}"
                return False, error_msg.strip(), execution_data
        
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            execution_data["execution_time"] = execution_time
            return False, f"Job timed out after {timeout} seconds", execution_data
        
        except FileNotFoundError:
            execution_time = time.time() - start_time
            execution_data["execution_time"] = execution_time
            return False, "Command not found", execution_data
        
        except Exception as e:
            execution_time = time.time() - start_time
            execution_data["execution_time"] = execution_time
            return False, f"Execution error: {str(e)}", execution_data

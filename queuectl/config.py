"""
Configuration management
"""
import json
import os
from pathlib import Path
from typing import Any, Optional


class Config:
    """Configuration manager with persistent storage"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.defaults = {
            "max_retries": 3,
            "backoff_base": 2.0,
            "worker_poll_interval": 1.0,
            "job_timeout": 300  # 5 minutes
        }
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file or use defaults"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = self.defaults.copy()
                    merged.update(config)
                    return merged
            except (json.JSONDecodeError, IOError):
                return self.defaults.copy()
        return self.defaults.copy()
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            raise RuntimeError(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self._config.get(key, default or self.defaults.get(key))
    
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        if key not in self.defaults:
            raise ValueError(f"Unknown configuration key: {key}")
        
        # Type validation
        if key == "max_retries" and not isinstance(value, int):
            raise ValueError("max_retries must be an integer")
        if key == "backoff_base" and not isinstance(value, (int, float)):
            raise ValueError("backoff_base must be a number")
        if key == "worker_poll_interval" and not isinstance(value, (int, float)):
            raise ValueError("worker_poll_interval must be a number")
        if key == "job_timeout" and not isinstance(value, int):
            raise ValueError("job_timeout must be an integer")
        
        self._config[key] = value
        self._save_config()
    
    def get_all(self) -> dict:
        """Get all configuration values"""
        return self._config.copy()
    
    def reset(self):
        """Reset configuration to defaults"""
        self._config = self.defaults.copy()
        self._save_config()


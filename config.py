"""
Configuration module for SpectraVortex API
Loads settings from .env file
"""

import os
from typing import Any, Optional
from dotenv import load_dotenv

# агружаем переменные окружения из .env файла
load_dotenv()

class APIConfig:
    """Configuration for SpectraVortex API"""
    
    # API Settings
    BASE_URL: str = os.getenv('API_BASE_URL', 'http://localhost:8000/api/v1')
    API_KEY: str = os.getenv('API_KEY', '')
    TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    
    # Development Settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Solver Settings
    MAX_ITERATIONS: int = int(os.getenv('MAX_ITERATIONS', '1000'))
    GRID_SIZE_LIMIT: int = int(os.getenv('GRID_SIZE_LIMIT', '500'))
    SOLVER_TIMEOUT: int = int(os.getenv('SOLVER_TIMEOUT', '60'))
    
    # Cache Settings
    CACHE_ENABLED: bool = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '300'))
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR: str = os.getenv('DATA_DIR', os.path.join(BASE_DIR, 'data'))
    LOGS_DIR: str = os.getenv('LOGS_DIR', os.path.join(BASE_DIR, 'logs'))
    
    # API Endpoints
    ENDPOINTS = {
        'health': '/health',
        'solve': '/solve',
        'validate': '/validate',
        'status': '/status/{task_id}',
        'problems': '/problems',
        'solutions': '/solutions/{task_id}'
    }
    
    @classmethod
    def get_endpoint(cls, name: str, **kwargs) -> str:
        """Get full endpoint URL"""
        if name not in cls.ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {name}")
        
        endpoint = cls.ENDPOINTS[name]
        # Replace path parameters
        for key, value in kwargs.items():
            endpoint = endpoint.replace(f'{{{key}}}', str(value))
        
        return f"{cls.BASE_URL}{endpoint}"
    
    @classmethod
    def get_headers(cls) -> dict:
        """Get default API headers"""
        return {
            'Authorization': f'Bearer {cls.API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'SpectraVortex-Client/1.0.0'
        }
    
    @classmethod
    def validate_config(cls) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        if not cls.API_KEY:
            issues.append("API_KEY is not set")
        
        if not cls.BASE_URL.startswith(('http://', 'https://')):
            issues.append(f"Invalid BASE_URL: {cls.BASE_URL}")
        
        if cls.TIMEOUT <= 0:
            issues.append(f"Invalid TIMEOUT: {cls.TIMEOUT}")
        
        return issues

# Create config instance
config = APIConfig()

# Validate configuration on import
if config.DEBUG:
    issues = config.validate_config()
    if issues:
        print("⚠️ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Configuration is valid")

# For backward compatibility
API_CONFIG = config

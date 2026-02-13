"""
SpectraVortex API Client
Handles communication with SpectraVortex API
"""

import requests
import json
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from config import config

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class SpectraVortexAPIClient:
    """Client for SpectraVortex API"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            api_key: API key (uses config.API_KEY if not provided)
            base_url: Base API URL (uses config.BASE_URL if not provided)
        """
        self.api_key = api_key or config.API_KEY
        self.base_url = base_url or config.BASE_URL
        self.timeout = config.TIMEOUT
        
        # Create session with connection pooling
        self.session = requests.Session()
        self.session.headers.update(config.get_headers())
        
        # Update Authorization header with provided api_key
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        
        logger.info(f"API Client initialized for {self.base_url}")
        
        # Simple cache for development
        self._cache = {}
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_cache: bool = False
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Make HTTP request to API
        
        Returns:
            Tuple of (success, response_data)
        """
        url = f"{self.base_url}{endpoint}"
        
        # Check cache
        cache_key = f"{method}:{url}:{json.dumps(params or {})}:{json.dumps(data or {})}"
        if use_cache and config.CACHE_ENABLED and cache_key in self._cache:
            cache_data = self._cache[cache_key]
            if time.time() - cache_data['timestamp'] < config.CACHE_TTL:
                logger.debug(f"Cache hit for {cache_key}")
                return True, cache_data['data']
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.timeout
                )
            elif method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    timeout=self.timeout
                )
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url, 
                    json=data, 
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Log request details in debug mode
            if config.DEBUG:
                logger.debug(f"Request: {method} {url}")
                if data:
                    logger.debug(f"Request data: {json.dumps(data, indent=2)}")
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Check response
            response.raise_for_status()
            
            # Parse JSON response
            if response.content:
                result = response.json()
            else:
                result = {}
            
            # Cache result if successful
            if use_cache and config.CACHE_ENABLED:
                self._cache[cache_key] = {
                    'timestamp': time.time(),
                    'data': result
                }
            
            return True, result
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return False, {'error': 'Request timeout', 'url': url}
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            return False, {'error': 'Connection error', 'url': url}
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code} for {url}")
            try:
                error_data = response.json()
            except:
                error_data = {'error': str(e)}
            return False, error_data
            
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return False, {'error': str(e), 'url': url}
    
    def health_check(self) -> bool:
        """Check if API is available"""
        success, response = self._make_request('GET', '/health')
        if success and response.get('status') == 'healthy':
            logger.info("API health check passed")
            return True
        else:
            logger.warning(f"API health check failed: {response}")
            return False
    
    def solve_problem(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit problem for solving
        
        Args:
            problem_data: Problem definition
            
        Returns:
            Dict with task_id and status
        """
        logger.info(f"Submitting problem: {problem_data.get('problem_type', 'unknown')}")
        
        success, response = self._make_request('POST', '/solve', data=problem_data)
        
        if success:
            logger.info(f"Problem submitted successfully. Task ID: {response.get('task_id')}")
            return {
                'status': 'submitted',
                'task_id': response.get('task_id'),
                'message': response.get('message', 'Problem accepted'),
                'estimated_time': response.get('estimated_time')
            }
        else:
            logger.error(f"Failed to submit problem: {response}")
            return {
                'status': 'error',
                'error': response.get('error', 'Unknown error'),
                'details': response
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task"""
        endpoint = f"/status/{task_id}"
        success, response = self._make_request('GET', endpoint)
        
        if success:
            return {
                'status': 'success',
                'task_id': task_id,
                'task_status': response.get('status'),
                'progress': response.get('progress'),
                'estimated_time_left': response.get('estimated_time_left')
            }
        else:
            return {
                'status': 'error',
                'task_id': task_id,
                'error': response.get('error', 'Failed to get status')
            }
    
    def get_solution(self, task_id: str, wait: bool = False, poll_interval: int = 2) -> Dict[str, Any]:
        """
        Get solution for a task
        
        Args:
            task_id: Task ID
            wait: If True, wait for solution to be ready
            poll_interval: How often to poll for status (seconds)
            
        Returns:
            Solution data
        """
        endpoint = f"/solutions/{task_id}"
        
        if wait:
            logger.info(f"Waiting for solution for task {task_id}")
            
            # Poll for status until ready or timeout
            start_time = time.time()
            while time.time() - start_time < config.SOLVER_TIMEOUT:
                status_info = self.get_task_status(task_id)
                
                if status_info['status'] == 'error':
                    return status_info
                
                task_status = status_info.get('task_status')
                
                if task_status == 'completed':
                    break  # Solution is ready
                elif task_status == 'failed':
                    return {
                        'status': 'error',
                        'task_id': task_id,
                        'error': 'Task failed',
                        'details': status_info
                    }
                elif task_status == 'processing':
                    # Still processing, wait and try again
                    progress = status_info.get('progress', 0)
                    logger.debug(f"Task {task_id} progress: {progress}%")
                    time.sleep(poll_interval)
                else:
                    # Unknown status
                    time.sleep(poll_interval)
            
            # Check if timeout reached
            if time.time() - start_time >= config.SOLVER_TIMEOUT:
                return {
                    'status': 'error',
                    'task_id': task_id,
                    'error': f'Timeout waiting for solution ({config.SOLVER_TIMEOUT}s)'
                }
        
        # Get the solution
        success, response = self._make_request('GET', endpoint)
        
        if success:
            logger.info(f"Solution retrieved for task {task_id}")
            return {
                'status': 'success',
                'task_id': task_id,
                'solution': response.get('solution'),
                'execution_time': response.get('execution_time'),
                'metadata': response.get('metadata', {})
            }
        else:
            logger.error(f"Failed to get solution for task {task_id}: {response}")
            return {
                'status': 'error',
                'task_id': task_id,
                'error': response.get('error', 'Failed to get solution'),
                'details': response
            }
    
    def validate_solution(self, problem_id: str, solution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a solution"""
        data = {
            'problem_id': problem_id,
            'solution': solution_data
        }
        
        success, response = self._make_request('POST', '/validate', data=data)
        
        if success:
            return {
                'status': 'success',
                'valid': response.get('valid', False),
                'score': response.get('score', 0),
                'feedback': response.get('feedback', ''),
                'details': response
            }
        else:
            return {
                'status': 'error',
                'valid': False,
                'error': response.get('error', 'Validation failed'),
                'details': response
            }
    
    def list_problems(self, problem_type: Optional[str] = None) -> Dict[str, Any]:
        """List available problems"""
        params = {}
        if problem_type:
            params['type'] = problem_type
        
        success, response = self._make_request('GET', '/problems', params=params)
        
        if success:
            return {
                'status': 'success',
                'problems': response.get('problems', []),
                'count': len(response.get('problems', []))
            }
        else:
            return {
                'status': 'error',
                'error': response.get('error', 'Failed to list problems'),
                'details': response
            }

# Create default client instance
default_client = SpectraVortexAPIClient()

def get_api_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> SpectraVortexAPIClient:
    """
    Get API client instance
    
    Args:
        api_key: Optional API key override
        base_url: Optional base URL override
        
    Returns:
        SpectraVortexAPIClient instance
    """
    if api_key or base_url:
        return SpectraVortexAPIClient(api_key=api_key, base_url=base_url)
    return default_client

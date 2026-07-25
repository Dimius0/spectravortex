"""
Deadlock protection mechanisms for production-ready routing.
Main features:
1. Timeout mechanism for A* algorithm
2. Fallback to alternative algorithms
3. Circuit breaker pattern for impossible routes
"""

import time
import signal
from functools import wraps
from typing import Optional, List, Tuple, Any
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoutingAlgorithm(Enum):
    """Available routing algorithms"""
    A_STAR = "a_star"
    WAVEFRONT = "wavefront"
    GEOMETRIC = "geometric"
    MAZE = "maze"
    TEES = "tees"

class RoutingError(Exception):
    """Base exception for routing failures"""
    pass


class TimeoutError(RoutingError):
    """Routing timeout exception"""
    pass


class DeadlockError(RoutingError):
    """Algorithm stuck in deadlock"""
    pass


class NoPathError(RoutingError):
    """No path exists with current constraints"""
    pass


@dataclass
class RouteResult:
    """Result of routing attempt"""
    path: Optional[List[Tuple[float, float]]]
    algorithm: RoutingAlgorithm
    time_spent: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class TimeoutContext:
    """Context manager for timeout control"""
    
    def __init__(self, seconds: float):
        self.seconds = seconds
        
    def __enter__(self):
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Routing timeout after {self.seconds} seconds")
        
        # Set up signal for Unix systems
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        except (AttributeError, ValueError):
            # Windows doesn't support SIGALRM
            self.start_time = time.time()
            self.timeout_handler = timeout_handler
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
        except (AttributeError, ValueError):
            # Windows fallback
            if hasattr(self, 'start_time'):
                elapsed = time.time() - self.start_time
                if elapsed > self.seconds:
                    raise TimeoutError(f"Routing timeout after {elapsed:.2f} seconds")


def timeout(seconds: float):
    """Decorator for function timeout"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with TimeoutContext(seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for routing failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Check if circuit is OPEN and recovery timeout has passed
            if self.state == "OPEN":
                if current_time - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise RoutingError(
                        f"Circuit breaker OPEN. "
                        f"Try again in {self.recovery_timeout - (current_time - self.last_failure_time):.0f} seconds"
                    )
            
            try:
                result = func(*args, **kwargs)
                
                # Success in HALF_OPEN state -> close the circuit
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker moving to CLOSED state")
                    
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = current_time
                
                # Check if we should open the circuit
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")
                
                raise e
        
        return wrapper


class DeadlockMonitor:
    """Monitors routing progress to detect deadlocks"""
    
    def __init__(self, max_iterations: int = 10000, check_interval: int = 100):
        self.max_iterations = max_iterations
        self.check_interval = check_interval
        self.iteration_count = 0
        self.last_progress_time = time.time()
        self.last_visited_count = 0
        
    def check(self, visited_nodes: int, current_node: Tuple[float, float], 
              target_node: Tuple[float, float]) -> bool:
        """Check for deadlock conditions"""
        self.iteration_count += 1
        
        # Check iteration limit
        if self.iteration_count > self.max_iterations:
            logger.warning(f"Max iterations reached: {self.max_iterations}")
            return False
        
        # Check progress every N iterations
        if self.iteration_count % self.check_interval == 0:
            current_time = time.time()
            time_since_progress = current_time - self.last_progress_time
            
            # No progress in last 2 seconds?
            if time_since_progress > 2.0:
                logger.warning(f"No progress for {time_since_progress:.1f} seconds")
                return False
            
            # Visited nodes not increasing?
            if visited_nodes <= self.last_visited_count:
                logger.warning(f"Visited nodes stuck at {visited_nodes}")
                return False
            
            self.last_visited_count = visited_nodes
            self.last_progress_time = current_time
        
        return True
    
    def reset(self):
        """Reset monitor for new routing attempt"""
        self.iteration_count = 0
        self.last_progress_time = time.time()
        self.last_visited_count = 0


# Проверьте этот файл, скопируйте его в проект и дайте знать, если всё ок.

"""
Adaptive multi-algorithm router with automatic fallback.
Implements production-grade routing with deadlock protection.
"""

import time
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import heapq
import logging
from collections import deque

from .deadlock_protection import (
    RoutingAlgorithm, RouteResult, TimeoutError,
    DeadlockError, NoPathError, RoutingError,
    timeout, CircuitBreaker, DeadlockMonitor
)

logger = logging.getLogger(__name__)


@dataclass
class RoutingRequest:
    """Routing request with all parameters"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    obstacles: List[Any]  # List of obstacle objects
    grid_size: float = 0.1  # microns
    max_iterations: int = 10000
    timeout_seconds: float = 1.0
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """Node for pathfinding algorithms"""
    x: float
    y: float
    g: float = 0  # Cost from start
    h: float = 0  # Heuristic to end
    f: float = 0  # Total cost
    parent: Optional['Node'] = None
    
    def __lt__(self, other):
        return self.f < other.f
    
    @property
    def pos(self):
        return (self.x, self.y)


class BaseRouter:
    """Base class for all routing algorithms"""
    
    def __init__(self, grid_size: float = 0.1):
        self.grid_size = grid_size
        self.obstacles = []
        
    def set_obstacles(self, obstacles: List[Any]):
        """Set obstacles for routing"""
        self.obstacles = obstacles
    
    def is_obstacle(self, x: float, y: float) -> bool:
        """Check if point is inside an obstacle"""
        for obstacle in self.obstacles:
            if self._point_in_obstacle(x, y, obstacle):
                return True
        return False
    
    def _point_in_obstacle(self, x: float, y: float, obstacle) -> bool:
        """Check if point is inside a rectangular obstacle"""
        # Simplified: obstacle is (x1, y1, x2, y2)
        if hasattr(obstacle, '__len__') and len(obstacle) == 4:
            x1, y1, x2, y2 = obstacle
            return x1 <= x <= x2 and y1 <= y <= y2
        return False
    
    def heuristic(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Euclidean distance heuristic"""
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    
    def get_neighbors(self, node: Node) -> List[Tuple[float, float]]:
        """Get valid neighboring positions (8-directional)"""
        x, y = node.x, node.y
        neighbors = []
        
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # 4-directional
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
        ]
        
        for dx, dy in directions:
            nx, ny = x + dx * self.grid_size, y + dy * self.grid_size
            if not self.is_obstacle(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors
    
    def reconstruct_path(self, node: Node) -> List[Tuple[float, float]]:
        """Reconstruct path from end node to start"""
        path = []
        current = node
        
        while current is not None:
            path.append((current.x, current.y))
            current = current.parent
        
        path.reverse()
        return path


class AStarRouter(BaseRouter):
    """A* pathfinding algorithm with deadlock protection"""
    
    def __init__(self, grid_size: float = 0.1):
        super().__init__(grid_size)
        self.monitor = DeadlockMonitor()
    
    @timeout(0.5)  # 500ms timeout for A*
    @CircuitBreaker(failure_threshold=3, recovery_timeout=30)
    def find_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """A* algorithm implementation"""
        logger.info(f"A* routing from {start} to {end}")
        
        start_node = Node(start[0], start[1])
        end_node = Node(end[0], end[1])
        
        open_set = []
        closed_set = set()
        node_dict = {}  # For quick lookup
        
        heapq.heappush(open_set, start_node)
        node_dict[start_node.pos] = start_node
        
        visited_count = 0
        current_position = start  # Initialize current position
        self.monitor.reset()
        
        while open_set:
            # Check for deadlock
            if not self.monitor.check(visited_count, current_position, end):
                raise DeadlockError("A* algorithm stuck in deadlock")
            
            current_node = heapq.heappop(open_set)
            current_position = current_node.pos  # Update current position
            visited_count += 1
            
            # Check if we reached the end
            if self.heuristic(current_node.pos, end_node.pos) < self.grid_size:
                logger.info(f"A* found path after visiting {visited_count} nodes")
                return self.reconstruct_path(current_node)
            
            closed_set.add(current_node.pos)
            
            # Explore neighbors
            for neighbor_pos in self.get_neighbors(current_node):
                if neighbor_pos in closed_set:
                    continue
                
                # Calculate costs
                g = current_node.g + self.heuristic(current_node.pos, neighbor_pos)
                h = self.heuristic(neighbor_pos, end_node.pos)
                f = g + h
                
                if neighbor_pos in node_dict:
                    neighbor_node = node_dict[neighbor_pos]
                    if g < neighbor_node.g:
                        neighbor_node.g = g
                        neighbor_node.h = h
                        neighbor_node.f = f
                        neighbor_node.parent = current_node
                        
                        # Update heap
                        if neighbor_node in open_set:
                            heapq.heapify(open_set)
                else:
                    neighbor_node = Node(
                        x=neighbor_pos[0],
                        y=neighbor_pos[1],
                        g=g, h=h, f=f,
                        parent=current_node
                    )
                    node_dict[neighbor_pos] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)
        
        raise NoPathError(f"No path found from {start} to {end}")


class WavefrontRouter(BaseRouter):
    """Wavefront (Lee algorithm) for guaranteed pathfinding"""
    
    def find_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Wavefront algorithm implementation"""
        logger.info(f"Wavefront routing from {start} to {end}")
        
        # Discretize space
        grid_width = int(abs(end[0] - start[0]) / self.grid_size) + 3
        grid_height = int(abs(end[1] - start[1]) / self.grid_size) + 3
        
        # Create wavefront grid
        grid = np.full((grid_height, grid_width), -1, dtype=int)
        
        # Convert to grid coordinates
        min_x = min(start[0], end[0]) - self.grid_size
        min_y = min(start[1], end[1]) - self.grid_size
        
        def to_grid(x, y):
            return (
                int((x - min_x) / self.grid_size),
                int((y - min_y) / self.grid_size)
            )
        
        def from_grid(gx, gy):
            return (
                min_x + gx * self.grid_size,
                min_y + gy * self.grid_size
            )
        
        start_gx, start_gy = to_grid(start[0], start[1])
        end_gx, end_gy = to_grid(end[0], end[1])
        
        # Mark obstacles
        for obstacle in self.obstacles:
            if hasattr(obstacle, '__len__') and len(obstacle) == 4:
                x1, y1, x2, y2 = obstacle
                gx1, gy1 = to_grid(x1, y1)
                gx2, gy2 = to_grid(x2, y2)
                
                for gx in range(gx1, gx2 + 1):
                    for gy in range(gy1, gy2 + 1):
                        if 0 <= gx < grid_width and 0 <= gy < grid_height:
                            grid[gy, gx] = -2  # Obstacle
        
        # Wavefront propagation
        queue = deque([(end_gx, end_gy, 0)])
        grid[end_gy, end_gx] = 0
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        while queue:
            gx, gy, dist = queue.popleft()
            
            for dx, dy in directions:
                ngx, ngy = gx + dx, gy + dy
                
                if (0 <= ngx < grid_width and 0 <= ngy < grid_height and
                    grid[ngy, ngx] == -1):
                    grid[ngy, ngx] = dist + 1
                    queue.append((ngx, ngy, dist + 1))
        
        # Check if start is reachable
        if grid[start_gy, start_gx] <= 0:
            raise NoPathError("Start not reachable in wavefront")
        
        # Backtrack to find path
        path = []
        gx, gy = start_gx, start_gy
        
        while (gx, gy) != (end_gx, end_gy):
            path.append(from_grid(gx, gy))
            
            # Find next step with lower distance
            current_dist = grid[gy, gx]
            next_pos = None
            
            for dx, dy in directions:
                ngx, ngy = gx + dx, gy + dy
                if (0 <= ngx < grid_width and 0 <= ngy < grid_height and
                    0 < grid[ngy, ngx] < current_dist):
                    current_dist = grid[ngy, ngx]
                    next_pos = (ngx, ngy)
            
            if next_pos is None:
                break
            
            gx, gy = next_pos
        
        path.append(from_grid(end_gx, end_gy))
        
        logger.info(f"Wavefront found path with {len(path)} points")
        return path


class GeometricRouter(BaseRouter):
    """Geometric routing (direct line with obstacle avoidance)"""
    
    def find_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Geometric routing implementation"""
        logger.info(f"Geometric routing from {start} to {end}")
        
        # Try direct line first
        if not self.line_intersects_obstacle(start, end):
            return [start, end]
        
        # Find obstacle-free path around obstacles
        path = [start]
        
        # Get bounding box of all obstacles
        obs_points = []
        for obstacle in self.obstacles:
            if hasattr(obstacle, '__len__') and len(obstacle) == 4:
                x1, y1, x2, y2 = obstacle
                obs_points.extend([(x1, y1), (x2, y2)])
        
        if obs_points:
            # Calculate safe path around obstacles
            min_x = min(p[0] for p in obs_points) - 2 * self.grid_size
            max_x = max(p[0] for p in obs_points) + 2 * self.grid_size
            min_y = min(p[1] for p in obs_points) - 2 * self.grid_size
            max_y = max(p[1] for p in obs_points) + 2 * self.grid_size
            
            # Create waypoints around obstacles
            if start[0] < min_x and end[0] > max_x:
                # Go above
                waypoint1 = (start[0], max_y + self.grid_size)
                waypoint2 = (end[0], max_y + self.grid_size)
                path.extend([waypoint1, waypoint2, end])
            elif start[1] < min_y and end[1] > max_y:
                # Go right
                waypoint1 = (max_x + self.grid_size, start[1])
                waypoint2 = (max_x + self.grid_size, end[1])
                path.extend([waypoint1, waypoint2, end])
            else:
                # More complex case - use A* for this segment
                a_star = AStarRouter(self.grid_size)
                a_star.set_obstacles(self.obstacles)
                return a_star.find_path(start, end)
        
        logger.info(f"Geometric routing found path with {len(path)} points")
        return path
    
    def line_intersects_obstacle(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
        """Check if line segment intersects any obstacle"""
        for obstacle in self.obstacles:
            if hasattr(obstacle, '__len__') and len(obstacle) == 4:
                x1, y1, x2, y2 = obstacle
                
                # Check if line segment intersects rectangle
                if self._line_intersects_rect(p1, p2, (x1, y1, x2, y2)):
                    return True
        
        return False
    
    def _line_intersects_rect(self, p1, p2, rect):
        """Check if line segment intersects rectangle"""
        # Implement line-rectangle intersection test
        # Simplified version
        x1, y1, x2, y2 = rect
        
        # Check if either endpoint is inside rectangle
        if (x1 <= p1[0] <= x2 and y1 <= p1[1] <= y2) or \
           (x1 <= p2[0] <= x2 and y1 <= p2[1] <= y2):
            return True
        
        # Check line segment against rectangle edges
        edges = [
            [(x1, y1), (x2, y1)],  # bottom
            [(x2, y1), (x2, y2)],  # right
            [(x2, y2), (x1, y2)],  # top
            [(x1, y2), (x1, y1)]   # left
        ]
        
        for e1, e2 in edges:
            if self._lines_intersect(p1, p2, e1, e2):
                return True
        
        return False
    
    def _lines_intersect(self, a1, a2, b1, b2):
        """Check if two line segments intersect"""
        # Using cross product method
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return (ccw(a1, b1, b2) != ccw(a2, b1, b2) and 
                ccw(a1, a2, b1) != ccw(a1, a2, b2))


class AdaptiveRouter:
    """
    Main adaptive router with multi-algorithm fallback.
    Production-ready with deadlock protection and timeout handling.
    """
    
    def __init__(self, grid_size: float = 0.1):
        self.grid_size = grid_size
        self.obstacles = []
        
        # Initialize routing algorithms
        self.algorithms = {
            RoutingAlgorithm.A_STAR: AStarRouter(grid_size),
            RoutingAlgorithm.WAVEFRONT: WavefrontRouter(grid_size),
            RoutingAlgorithm.GEOMETRIC: GeometricRouter(grid_size),
        }
        
        # Algorithm priority for fallback
        self.algorithm_priority = [
            RoutingAlgorithm.A_STAR,      # Fast, good for simple cases
            RoutingAlgorithm.GEOMETRIC,   # Good for sparse obstacles
            RoutingAlgorithm.WAVEFRONT,   # Guaranteed but slower
        ]
        
        # Statistics for adaptive routing
        self.stats = {
            algo: {"success": 0, "failures": 0, "total_time": 0.0}
            for algo in self.algorithms.keys()
        }
        
        # Cache for impossible routes
        self.impossible_routes_cache = set()
    
    def set_obstacles(self, obstacles: List[Any]):
        """Set obstacles for all algorithms"""
        self.obstacles = obstacles
        for algo in self.algorithms.values():
            algo.set_obstacles(obstacles)
    
    def find_path(self, start: Tuple[float, float], end: Tuple[float, float], 
                  max_attempts: int = 3) -> RouteResult:
        """
        Find path with adaptive algorithm selection and fallback.
        
        Args:
            start: Start position (x, y)
            end: End position (x, y)
            max_attempts: Maximum number of algorithm attempts
            
        Returns:
            RouteResult with path and metadata
        """
        logger.info(f"=== Adaptive routing from {start} to {end} ===")
        
        # Check cache for impossible routes
        cache_key = f"{start}_{end}"
        if cache_key in self.impossible_routes_cache:
            logger.warning(f"Route in cache as impossible: {start} -> {end}")
            return RouteResult(
                path=None,
                algorithm=RoutingAlgorithm.A_STAR,
                time_spent=0,
                success=False,
                error_message="Route previously marked as impossible"
            )
        
        # Try algorithms in priority order
        for attempt in range(max_attempts):
            for algo_name in self.algorithm_priority:
                algo = self.algorithms[algo_name]
                
                logger.info(f"Attempt {attempt + 1}: {algo_name.value}")
                
                start_time = time.time()
                
                try:
                    path = algo.find_path(start, end)
                    elapsed = time.time() - start_time
                    
                    # Update statistics
                    self.stats[algo_name]["success"] += 1
                    self.stats[algo_name]["total_time"] += elapsed
                    
                    logger.info(f"{algo_name.value} succeeded in {elapsed:.3f}s")
                    
                    return RouteResult(
                        path=path,
                        algorithm=algo_name,
                        time_spent=elapsed,
                        success=True,
                        metadata={
                            "attempt": attempt + 1,
                            "algorithm": algo_name.value,
                            "path_length": len(path),
                            "visited_nodes": "N/A"
                        }
                    )
                    
                except TimeoutError as e:
                    elapsed = time.time() - start_time
                    self.stats[algo_name]["failures"] += 1
                    logger.warning(f"{algo_name.value} timeout: {e}")
                    
                except (DeadlockError, NoPathError) as e:
                    elapsed = time.time() - start_time
                    self.stats[algo_name]["failures"] += 1
                    logger.warning(f"{algo_name.value} failed: {e}")
                    
                    # If wavefront fails, route is likely impossible
                    if algo_name == RoutingAlgorithm.WAVEFRONT:
                        self.impossible_routes_cache.add(cache_key)
                        logger.error(f"Route marked as impossible: {start} -> {end}")
                        
                        return RouteResult(
                            path=None,
                            algorithm=algo_name,
                            time_spent=elapsed,
                            success=False,
                            error_message=f"All algorithms failed: {e}"
                        )
        
        # All attempts failed
        error_msg = f"Failed after {max_attempts} attempts with all algorithms"
        logger.error(error_msg)
        
        return RouteResult(
            path=None,
            algorithm=RoutingAlgorithm.A_STAR,
            time_spent=0,
            success=False,
            error_message=error_msg
        )
    
    def get_statistics(self) -> Dict:
        """Get routing statistics"""
        stats = {}
        for algo_name, algo_stats in self.stats.items():
            total = algo_stats["success"] + algo_stats["failures"]
            if total > 0:
                success_rate = algo_stats["success"] / total * 100
                avg_time = algo_stats["total_time"] / algo_stats["success"] if algo_stats["success"] > 0 else 0
            else:
                success_rate = 0
                avg_time = 0
            
            stats[algo_name.value] = {
                "success": algo_stats["success"],
                "failures": algo_stats["failures"],
                "success_rate": f"{success_rate:.1f}%",
                "avg_time_ms": f"{avg_time * 1000:.1f}",
                "total_time": f"{algo_stats['total_time']:.3f}s"
            }
        
        stats["cache_size"] = len(self.impossible_routes_cache)
        return stats
    
    def clear_cache(self):
        """Clear impossible routes cache"""
        self.impossible_routes_cache.clear()
        logger.info("Impossible routes cache cleared")


# Factory function for easy router creation
def create_adaptive_router(grid_size: float = 0.1) -> AdaptiveRouter:
    """Factory function to create adaptive router"""
    return AdaptiveRouter(grid_size)

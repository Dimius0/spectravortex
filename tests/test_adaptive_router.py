"""
Comprehensive tests for adaptive router with deadlock protection.
Tests cover all algorithms and edge cases.
"""

import pytest
import numpy as np
import time
import sys
from typing import List, Tuple

from router.adaptive_router import (
    AdaptiveRouter, create_adaptive_router,
    AStarRouter, WavefrontRouter, GeometricRouter,
    RouteResult, RoutingAlgorithm
)
from router.deadlock_protection import (
    TimeoutError, DeadlockError, NoPathError
)


class TestBaseRouter:
    """Base router functionality tests"""
    
    def test_heuristic_calculation(self):
        """Test distance heuristic calculation"""
        router = AdaptiveRouter(grid_size=0.1)
        
        # Euclidean distance
        dist = router.algorithms[RoutingAlgorithm.A_STAR].heuristic(
            (0, 0), (3, 4)
        )
        assert abs(dist - 5.0) < 0.001  # 3-4-5 triangle
        
        # Zero distance
        dist = router.algorithms[RoutingAlgorithm.A_STAR].heuristic(
            (1, 2), (1, 2)
        )
        assert dist == 0.0
    
    def test_obstacle_detection(self):
        """Test obstacle detection"""
        router = AdaptiveRouter(grid_size=0.1)
        
        # Create obstacles
        obstacles = [
            (1.0, 1.0, 2.0, 2.0),  # Square from (1,1) to (2,2)
            (3.0, 3.0, 4.0, 4.0)   # Another square
        ]
        router.set_obstacles(obstacles)
        
        # Test points inside obstacles
        a_star = router.algorithms[RoutingAlgorithm.A_STAR]
        assert a_star.is_obstacle(1.5, 1.5)
        assert a_star.is_obstacle(3.5, 3.5)
        
        # Test points outside obstacles
        assert not a_star.is_obstacle(0.5, 0.5)
        assert not a_star.is_obstacle(2.5, 2.5)


class TestAStarRouter:
    """A* algorithm specific tests"""
    
    def test_simple_path_no_obstacles(self):
        """A* should find straight line path without obstacles"""
        router = AStarRouter(grid_size=0.1)
        
        # Simple diagonal path
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        path = router.find_path(start, end)
        
        assert len(path) >= 2
        assert path[0] == start
        assert path[-1] == end
        
        # Check path is roughly diagonal
        for point in path:
            # Points should be close to line y = x
            assert abs(point[0] - point[1]) < 0.2
    
    def test_path_around_single_obstacle(self):
        """A* should navigate around a single obstacle"""
        router = AStarRouter(grid_size=0.1)
        
        # Put obstacle in the middle
        obstacles = [(0.4, 0.4, 0.6, 0.6)]
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        path = router.find_path(start, end)
        
        assert len(path) > 2  # Should have waypoints
        assert path[0] == start
        assert path[-1] == end
        
        # Verify path doesn't go through obstacle
        for point in path:
            x, y = point
            assert not (0.4 <= x <= 0.6 and 0.4 <= y <= 0.6)
    
    def test_no_path_scenario(self):
        """A* should raise exception when no path exists"""
        router = AStarRouter(grid_size=0.1)
        
        # Create wall completely blocking the path
        obstacles = [(0.3, -0.5, 0.7, 1.5)]  # Vertical wall
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        with pytest.raises(NoPathError):
            router.find_path(start, end)
    
    @pytest.mark.slow
    def test_timeout_protection(self):
        """Test that A* times out on impossible maze"""
        router = AStarRouter(grid_size=0.05)  # Fine grid
        
        # Create complex maze that will take too long
        obstacles = []
        for i in range(20):
            obstacles.append((i * 0.1, 0.0, i * 0.1 + 0.05, 2.0))
        
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (2.0, 2.0)
        
        # This should timeout due to @timeout(0.5) decorator
        with pytest.raises(TimeoutError):
            router.find_path(start, end)


class TestWavefrontRouter:
    """Wavefront algorithm tests"""
    
    def test_wavefront_simple_path(self):
        """Wavefront should find path in simple case"""
        router = WavefrontRouter(grid_size=0.1)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        path = router.find_path(start, end)
        
        assert len(path) >= 2
        assert path[0] == start
        assert path[-1] == end
    
    def test_wavefront_maze(self):
        """Wavefront should solve maze"""
        router = WavefrontRouter(grid_size=0.1)
        
        # Create corridor maze
        obstacles = [
            (0.2, -0.1, 0.4, 0.6),   # Left block
            (0.6, 0.4, 0.8, 1.1),    # Right block
        ]
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        path = router.find_path(start, end)
        
        assert path is not None
        assert len(path) > 2
        assert path[0] == start
        assert path[-1] == end
    
    def test_wavefront_no_path(self):
        """Wavefront should detect impossible paths"""
        router = WavefrontRouter(grid_size=0.1)
        
        # Completely enclosed area
        obstacles = [
            (-0.1, -0.1, 1.1, 0.1),  # Bottom wall
            (-0.1, 0.9, 1.1, 1.1),   # Top wall
            (-0.1, -0.1, 0.1, 1.1),  # Left wall
            (0.9, -0.1, 1.1, 1.1),   # Right wall
        ]
        router.set_obstacles(obstacles)
        
        start = (0.5, 0.5)
        end = (2.0, 2.0)  # Outside the box
        
        with pytest.raises(NoPathError):
            router.find_path(start, end)


class TestGeometricRouter:
    """Geometric routing tests"""
    
    def test_direct_line_no_obstacles(self):
        """Geometric router should return straight line"""
        router = GeometricRouter(grid_size=0.1)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        path = router.find_path(start, end)
        
        assert path == [start, end]  # Direct line
    
    def test_obstacle_avoidance(self):
        """Geometric router should go around obstacles"""
        router = GeometricRouter(grid_size=0.1)
        
        # Obstacle in direct path
        obstacles = [(0.4, 0.4, 0.6, 0.6)]
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        path = router.find_path(start, end)
        
        assert len(path) > 2  # Should have waypoints
        assert path[0] == start
        assert path[-1] == end
        
        # Check it avoids obstacle
        for point in path:
            x, y = point
            assert not (0.4 <= x <= 0.6 and 0.4 <= y <= 0.6)
    
    def test_fallback_to_astar(self):
        """Geometric router should fall back to A* for complex cases"""
        router = GeometricRouter(grid_size=0.1)
        
        # Create L-shaped obstacle that geometric can't handle simply
        obstacles = [
            (0.3, 0.3, 0.7, 0.4),  # Horizontal bar
            (0.6, 0.3, 0.7, 0.7),  # Vertical bar
        ]
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        # This should trigger A* fallback
        path = router.find_path(start, end)
        
        assert path is not None
        assert len(path) >= 2


class TestAdaptiveRouterIntegration:
    """Integration tests for adaptive router"""
    
    def test_adaptive_router_creation(self):
        """Test factory function creates router correctly"""
        router = create_adaptive_router(grid_size=0.2)
        assert isinstance(router, AdaptiveRouter)
        assert router.grid_size == 0.2
        
        # Should have all algorithms
        assert RoutingAlgorithm.A_STAR in router.algorithms
        assert RoutingAlgorithm.WAVEFRONT in router.algorithms
        assert RoutingAlgorithm.GEOMETRIC in router.algorithms
    
    def test_simple_routing_adaptive(self):
        """Adaptive router should handle simple case"""
        router = create_adaptive_router(grid_size=0.1)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        result = router.find_path(start, end)
        
        assert result.success
        assert result.algorithm == RoutingAlgorithm.A_STAR  # First choice
        assert len(result.path) >= 2
        assert result.path[0] == start
        assert result.path[-1] == end
    
    def test_algorithm_fallback(self):
        """Adaptive router should fallback when A* fails"""
        router = create_adaptive_router(grid_size=0.1)
        
        # Create maze that will timeout A* but wavefront can solve
        obstacles = []
        for i in range(5):  # Simple maze, not too complex
            obstacles.append((0.3, i * 0.2, 0.7, i * 0.2 + 0.1))
        
        router.set_obstacles(obstacles)
        
        start = (0.0, 0.0)
        end = (1.0, 1.0)
        
        # Mock A* to always timeout for this test
        original_find_path = router.algorithms[RoutingAlgorithm.A_STAR].find_path
        def mock_timeout(*args, **kwargs):
            time.sleep(0.6)  # Exceed 0.5s timeout
            raise TimeoutError("Mock timeout")
        
        router.algorithms[RoutingAlgorithm.A_STAR].find_path = mock_timeout
        
        try:
            result = router.find_path(start, end, max_attempts=2)
            
            # Should succeed with fallback algorithm
            assert result.success
            assert result.algorithm in [RoutingAlgorithm.GEOMETRIC, 
                                       RoutingAlgorithm.WAVEFRONT]
        finally:
            # Restore original method
            router.algorithms[RoutingAlgorithm.A_STAR].find_path = original_find_path
    
    def test_impossible_route_caching(self):
        """Test that impossible routes are cached"""
        router = create_adaptive_router(grid_size=0.1)
        
        # Create completely blocked scenario
        obstacles = [
            (-0.1, -0.1, 1.1, 0.1),  # Bottom wall
            (-0.1, 0.9, 1.1, 1.1),   # Top wall
            (-0.1, -0.1, 0.1, 1.1),  # Left wall
            (0.9, -0.1, 1.1, 1.1),   # Right wall
        ]
        router.set_obstacles(obstacles)
        
        start = (0.5, 0.5)
        end = (2.0, 2.0)  # Outside the box
        
        # First attempt should fail
        result1 = router.find_path(start, end)
        assert not result1.success
        
        # Check cache was populated
        cache_key = f"{start}_{end}"
        assert cache_key in router.impossible_routes_cache
        
        # Second attempt should return cached result immediately
        result2 = router.find_path(start, end)
        assert not result2.success
        assert "previously marked as impossible" in result2.error_message
    
    def test_statistics_tracking(self):
        """Test that router tracks statistics correctly"""
        router = create_adaptive_router(grid_size=0.1)
        
        # Run several routing attempts
        test_cases = [
            ((0.0, 0.0), (1.0, 1.0)),
            ((0.0, 1.0), (1.0, 0.0)),
            ((0.5, 0.5), (0.8, 0.8)),
        ]
        
        for start, end in test_cases:
            result = router.find_path(start, end)
            assert result.success
        
        # Get statistics
        stats = router.get_statistics()
        
        # Should have stats for all algorithms
        assert "a_star" in stats
        assert "wavefront" in stats
        assert "geometric" in stats
        
        # A* should have successes
        assert stats["a_star"]["success"] > 0
        
        # Print stats for debugging
        print("\nRouting Statistics:")
        for algo, algo_stats in stats.items():
            print(f"  {algo}: {algo_stats}")
    
    @pytest.mark.performance
    def test_performance_basic(self):
        """Basic performance test"""
        router = create_adaptive_router(grid_size=0.1)
        
        start = (0.0, 0.0)
        end = (5.0, 5.0)  # Longer path
        
        start_time = time.time()
        result = router.find_path(start, end)
        elapsed = time.time() - start_time
        
        assert result.success
        assert elapsed < 2.0  # Should complete in under 2 seconds
        
        print(f"\nPerformance: routed {start} to {end} in {elapsed:.3f}s")
        print(f"Path length: {len(result.path)} points")


class TestEdgeCases:
    """Edge case and stress tests"""
    
    def test_zero_length_path(self):
        """Test routing from point to itself"""
        router = create_adaptive_router(grid_size=0.1)
        
        start = end = (0.5, 0.5)
        
        result = router.find_path(start, end)
        
        assert result.success
        assert len(result.path) >= 1
        assert result.path[0] == start
        # May have 1 or more points (some algorithms add start+end)
    
    def test_very_close_points(self):
        """Test routing between very close points"""
        router = create_adaptive_router(grid_size=0.01)  # Fine grid
        
        start = (0.0, 0.0)
        end = (0.001, 0.001)  # Very close
        
        result = router.find_path(start, end)
        
        assert result.success
        assert result.path[-1] == end
    
    def test_large_coordinates(self):
        """Test routing with large coordinates"""
        router = create_adaptive_router(grid_size=1.0)  # Coarse grid for speed
        
        start = (0.0, 0.0)
        end = (100.0, 100.0)  # Large distance
        
        result = router.find_path(start, end)
        
        assert result.success
        assert result.path[0] == start
        assert result.path[-1] == end
    
    def test_obstacle_at_start_or_end(self):
        """Test routing when start or end is inside obstacle"""
        router = create_adaptive_router(grid_size=0.1)
        
        # Obstacle covering start point
        obstacles = [(0.0, 0.0, 0.5, 0.5)]
        router.set_obstacles(obstacles)
        
        start = (0.2, 0.2)  # Inside obstacle
        end = (1.0, 1.0)
        
        # Should fail or find creative path
        result = router.find_path(start, end)
        
        # Either fails or succeeds with path starting outside obstacle
        if result.success:
            assert result.path[0] != start  # Can't start in obstacle
        else:
            assert "impossible" in result.error_message.lower()
    
    def test_many_obstacles(self):
        """Stress test with many obstacles"""
        router = create_adaptive_router(grid_size=0.2)  # Coarser for speed
        
        # Create grid of obstacles
        obstacles = []
        for i in range(5):
            for j in range(5):
                if (i + j) % 2 == 0:  # Checkerboard pattern
                    x1, y1 = i * 0.4, j * 0.4
                    x2, y2 = x1 + 0.3, y1 + 0.3
                    obstacles.append((x1, y1, x2, y2))
        
        router.set_obstacles(obstacles)
        
        start = (0.05, 0.05)  # In empty space
        end = (1.95, 1.95)    # In empty space
        
        result = router.find_path(start, end)
        
        # Should find path through checkerboard
        assert result.success
        
        # Verify path avoids obstacles
        for point in result.path:
            x, y = point
            in_obstacle = False
            for ox1, oy1, ox2, oy2 in obstacles:
                if ox1 <= x <= ox2 and oy1 <= y <= oy2:
                    in_obstacle = True
                    break
            assert not in_obstacle, f"Path point {point} is inside obstacle"


def run_all_tests():
    """Run all tests and print summary"""
    print("=" * 60)
    print("Running Adaptive Router Tests")
    print("=" * 60)
    
    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings",
    ])
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    # Run tests when script is executed directly
    sys.exit(run_all_tests())

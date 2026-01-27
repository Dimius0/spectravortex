"""
FAST tests for adaptive router - only fast tests without timeouts and complex mazes.
All tests should complete in < 2 seconds.
"""

import pytest
import numpy as np
import time
import sys
from typing import List, Tuple

from router.adaptive_router import (
    AdaptiveRouter, create_adaptive_router,
    AStarRouter, WavefrontRouter, GeometricRouter,
    RouteResult, RoutingAlgorithm, point_equal
)
from router.deadlock_protection import (
    TimeoutError, DeadlockError, NoPathError
)


class TestBaseRouterFast:
    """Base router functionality tests - FAST"""

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


class TestAStarRouterFast:
    """A* algorithm specific tests - FAST only"""

    def setup_method(self):
        """Reset circuit breaker before each test"""
        self.router = AStarRouter(grid_size=0.1)

    def test_simple_path_no_obstacles(self):
        """A* should find straight line path without obstacles"""
        # Simple diagonal path
        start = (0.0, 0.0)
        end = (1.0, 1.0)

        path = self.router.find_path(start, end)

        assert len(path) >= 2
        assert point_equal(path[0], start)
        assert point_equal(path[-1], end)

    def test_path_around_single_obstacle(self):
        """A* should navigate around a single obstacle"""
        # Put obstacle in the middle
        obstacles = [(0.4, 0.4, 0.6, 0.6)]
        self.router.set_obstacles(obstacles)

        start = (0.0, 0.0)
        end = (1.0, 1.0)

        path = self.router.find_path(start, end)

        assert len(path) > 2  # Should have waypoints
        assert point_equal(path[0], start)
        assert point_equal(path[-1], end)

        # Verify path doesn't go through obstacle
        for point in path:
            x, y = point
            assert not (0.4 <= x <= 0.6 and 0.4 <= y <= 0.6)

    def test_no_path_scenario_fast(self):
        """A* should raise exception when no path exists - FIXED version"""
        # Create truly impossible scenario: sealed room
        obstacles = [
            # Outer walls (completely sealed)
            (-1.0, -1.0, 2.0, 0.0),   # Bottom wall (extended)
            (-1.0, 1.0, 2.0, 2.0),    # Top wall (extended)
            (-1.0, -1.0, 0.0, 2.0),   # Left wall (extended)
            (1.0, -1.0, 2.0, 2.0),    # Right wall (extended)
            # Internal block
            (0.2, 0.2, 0.8, 0.8)      # Solid block in center
        ]
        self.router.set_obstacles(obstacles)

        start = (0.1, 0.1)  # Inside sealed area
        end = (1.5, 1.5)    # Outside

        # Should NOT find a path
        with pytest.raises(NoPathError):
            self.router.find_path(start, end)


class TestWavefrontRouterFast:
    """Wavefront algorithm tests - FAST only"""

    def setup_method(self):
        self.router = WavefrontRouter(grid_size=0.1)

    def test_wavefront_simple_path(self):
        """Wavefront should find path in simple case"""
        start = (0.0, 0.0)
        end = (1.0, 1.0)

        path = self.router.find_path(start, end)

        assert len(path) >= 2
        assert point_equal(path[0], start)
        assert point_equal(path[-1], end)

    def test_wavefront_simple_maze(self):
        """Wavefront should solve simple maze - FIXED version"""
        # Single obstacle that doesn't completely block
        obstacles = [(0.3, 0.3, 0.7, 0.4)]  # Horizontal block, not too thick
        self.router.set_obstacles(obstacles)

        start = (0.0, 0.0)
        end = (1.0, 1.0)

        path = self.router.find_path(start, end)

        assert path is not None
        assert len(path) > 2
        assert point_equal(path[0], start)
        assert point_equal(path[-1], end)

    def test_wavefront_no_path(self):
        """Wavefront should detect impossible paths"""
        # Simple enclosed area
        obstacles = [
            (0.0, 0.0, 1.0, 0.1),   # Bottom wall
            (0.0, 0.9, 1.0, 1.0),   # Top wall
            (0.0, 0.0, 0.1, 1.0),   # Left wall
            (0.9, 0.0, 1.0, 1.0),   # Right wall
        ]
        self.router.set_obstacles(obstacles)

        start = (0.5, 0.5)
        end = (2.0, 2.0)  # Outside the box

        with pytest.raises(NoPathError):
            self.router.find_path(start, end)


class TestGeometricRouterFast:
    """Geometric routing tests - FAST only"""

    def setup_method(self):
        self.router = GeometricRouter(grid_size=0.1)

    def test_direct_line_no_obstacles(self):
        """Geometric router should return straight line"""
        start = (0.0, 0.0)
        end = (1.0, 1.0)

        path = self.router.find_path(start, end)

        assert path == [start, end]  # Direct line

    def test_obstacle_avoidance(self):
        """Geometric router should go around obstacles"""
        # Obstacle in direct path
        obstacles = [(0.4, 0.4, 0.6, 0.6)]
        self.router.set_obstacles(obstacles)

        start = (0.0, 0.0)
        end = (1.0, 1.0)

        path = self.router.find_path(start, end)

        assert len(path) > 2  # Should have waypoints
        assert point_equal(path[0], start)
        assert point_equal(path[-1], end)

        # Check it avoids obstacle
        for point in path:
            x, y = point
            assert not (0.4 <= x <= 0.6 and 0.4 <= y <= 0.6)


class TestAdaptiveRouterIntegrationFast:
    """Integration tests for adaptive router - FAST only"""

    def setup_method(self):
        """Create fresh router for each test"""
        self.router = create_adaptive_router(grid_size=0.1)

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
        start = (0.0, 0.0)
        end = (1.0, 1.0)

        result = self.router.find_path(start, end)

        assert result.success
        assert result.algorithm == RoutingAlgorithm.A_STAR  # First choice
        assert len(result.path) >= 2
        assert point_equal(result.path[0], start)
        assert point_equal(result.path[-1], end)

    def test_impossible_route_caching_fast(self):
        """Test that impossible routes are cached - FIXED with solid block"""
        # Create SOLID BOX - start completely surrounded
        obstacles = [
            # Create a cross-shaped obstacle that blocks all directions
            (0.3, 0.0, 0.7, 1.0),  # Vertical wall
            (0.0, 0.3, 1.0, 0.7),  # Horizontal wall
        ]
        self.router.set_obstacles(obstacles)

        # Start and end in opposite quadrants (completely separated by cross)
        start = (0.2, 0.2)  # Bottom-left quadrant
        end = (0.8, 0.8)    # Top-right quadrant

        # First attempt should fail (cross blocks all paths)
        result1 = self.router.find_path(start, end)
        
        # Debug output if test fails
        if result1.success:
            print(f"DEBUG: Found unexpected path: {result1.path}")
            print(f"DEBUG: Obstacles: {obstacles}")
            print(f"DEBUG: Grid size: {self.router.grid_size}")
            print(f"DEBUG: Algorithm used: {result1.algorithm}")
        
        assert not result1.success, (
            f"Expected failure but got success.\n"
            f"Path: {result1.path}\n"
            f"Obstacles: {obstacles}\n"
            f"Grid size: {self.router.grid_size}"
        )

        # Check cache was populated
        cache_key = f"{start}_{end}"
        assert cache_key in self.router.impossible_routes_cache

        # Second attempt should return cached result immediately
        result2 = self.router.find_path(start, end)
        assert not result2.success
        assert "previously marked as impossible" in result2.error_message.lower()

    def test_statistics_tracking_fast(self):
        """Test that router tracks statistics correctly - FAST"""
        # Run several routing attempts
        test_cases = [
            ((0.0, 0.0), (1.0, 1.0)),
            ((0.0, 1.0), (1.0, 0.0)),
            ((0.5, 0.5), (0.8, 0.8)),
        ]

        for start, end in test_cases:
            result = self.router.find_path(start, end)
            assert result.success

        # Get statistics
        stats = self.router.get_statistics()

        # Should have stats for all algorithms
        assert "a_star" in stats
        assert "wavefront" in stats
        assert "geometric" in stats

        # A* should have successes
        assert stats["a_star"]["success"] > 0


class TestEdgeCasesFast:
    """Edge case and stress tests - FAST only"""

    def setup_method(self):
        self.router = create_adaptive_router(grid_size=0.1)

    def test_zero_length_path(self):
        """Test routing from point to itself"""
        start = end = (0.5, 0.5)

        result = self.router.find_path(start, end)

        assert result.success
        assert len(result.path) >= 1
        assert point_equal(result.path[0], start)

    def test_very_close_points(self):
        """Test routing between very close points"""
        router = create_adaptive_router(grid_size=0.05)  # Fine grid but not too fine
        
        start = (0.0, 0.0)
        end = (0.1, 0.1)  # Close but not extremely
        
        result = router.find_path(start, end)
        
        assert result.success
        assert point_equal(result.path[-1], end)

    def test_obstacle_at_start_or_end_fast(self):
        """Test routing when start or end is inside obstacle - FAST"""
        # Obstacle covering start point
        obstacles = [(0.0, 0.0, 0.5, 0.5)]
        self.router.set_obstacles(obstacles)

        start = (0.2, 0.2)  # Inside obstacle
        end = (1.0, 1.0)

        # Should fail (can't start in obstacle)
        result = self.router.find_path(start, end)
        assert not result.success

        # Check error message contains relevant info
        error_lower = result.error_message.lower()
        assert any(keyword in error_lower for keyword in
                   ['impossible', 'not reachable', 'failed', 'start'])

    def test_many_obstacles_fast(self):
        """Stress test with many obstacles - SAFE version"""
        router = create_adaptive_router(grid_size=0.2)  # Coarser for speed

        # Create widely spaced obstacles (2x2 grid)
        obstacles = []
        for i in range(2):
            for j in range(2):
                if (i + j) % 2 == 0:  # Checkerboard pattern
                    x1, y1 = i * 0.8, j * 0.8  # Large spacing
                    x2, y2 = x1 + 0.3, y1 + 0.3
                    obstacles.append((x1, y1, x2, y2))
        
        router.set_obstacles(obstacles)

        # Start and end in clear areas (between obstacles)
        # Obstacles at: (0,0)-(0.3,0.3) and (0.8,0.8)-(1.1,1.1)
        # Clear space around (0.5,0.5)
        start = (0.5, 0.5)  # Clear space between obstacles
        end = (1.3, 1.3)    # Clear space beyond

        result = router.find_path(start, end)

        # Should find path through checkerboard
        assert result.success, f"Failed to find path. Error: {result.error_message}"

        # Verify path avoids obstacles (with generous tolerance)
        for point in result.path:
            x, y = point
            in_obstacle = False
            for ox1, oy1, ox2, oy2 in obstacles:
                # Generous tolerance for grid boundaries and float errors
                # Make sure we're not inside or too close to obstacles
                if (ox1 - 0.2 <= x <= ox2 + 0.2 and 
                    oy1 - 0.2 <= y <= oy2 + 0.2):
                    in_obstacle = True
                    break
            assert not in_obstacle, (
                f"Path point {point} is too close to obstacle at "
                f"({ox1}, {oy1})-({ox2}, {oy2})\n"
                f"All obstacles: {obstacles}"
            )


def run_fast_tests():
    """Run all fast tests and print summary"""
    print("=" * 60)
    print("Running FAST Adaptive Router Tests")
    print("=" * 60)

    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings",
    ])

    if exit_code == 0:
        print("\n✅ All FAST tests passed!")
    else:
        print(f"\n❌ FAST tests failed with exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    # Run tests when script is executed directly
    sys.exit(run_fast_tests())

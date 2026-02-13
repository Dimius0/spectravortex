"""
Recursive Solver for Fractal Computation Architecture.
Implements recursive problem decomposition and hierarchical stitching.
"""

import logging
import time
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

from simulator.core.solver import Solver
from simulator.core.data_interface import FieldSolution
from simulator.core.solver_manager import SolverManager, create_solver_manager

logger = logging.getLogger(__name__)


@dataclass
class RecursionNode:
    """Node in the recursion tree."""
    node_id: str
    problem: Dict[str, Any]
    depth: int
    complexity: float
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    solved: bool = False
    solution: Optional[FieldSolution] = None


class RecursiveSolver(Solver):
    """
    Solver that implements recursive problem decomposition.
    
    This is the core of Phase 3.2: Fractal design capability.
    Features:
    - Recursive decomposition based on problem complexity
    - Hierarchical stitching of solutions
    - Fractal computation patterns
    - Automatic depth control
    """
    
    def __init__(self, name: str = "RecursiveSolver", version: str = "1.0"):
        super().__init__(name=name)
        self.version = version
        self.max_recursion_depth = 4
        self.min_problem_complexity = 5  # Scale from 1-10
        self.min_subproblem_size = 10    # Minimum size for decomposition
        self.decomposition_strategy = "adaptive"
        self.recursion_tree: Dict[str, RecursionNode] = {}
        self._visited_nodes = set()
        
        # Performance tracking
        self.decomposition_count = 0
        self.direct_solve_count = 0
        self.max_depth_reached = 0
        
        logger.info(f"Initialized {self.name} v{self.version}")

    def can_solve(self, problem: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Check if this solver can solve the given problem.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            Tuple of (can_solve, confidence)
        """
        try:
            analysis = self.analyze_problem(problem)
            complexity = analysis['complexity']
            
            # Higher confidence for complex problems
            if complexity >= 7:
                confidence = 0.9
            elif complexity >= 5:
                confidence = 0.7
            elif 'recursive' in problem.get('solver_preference', ''):
                confidence = 0.8
            elif problem.get('requires_decomposition', False):
                confidence = 0.85
            else:
                confidence = 0.3
            
            # Check for specific problem types
            problem_type = problem.get('problem_type', '')
            if problem_type in ['complex_waveguide', 'multi_domain', 'fractal_design', 'recursive']:
                confidence = min(confidence + 0.1, 1.0)
            
            # Check for recursion hints
            if problem.get('requires_recursion', False):
                confidence = min(confidence + 0.15, 1.0)
                
            if 'recursive' in problem.get('tags', []):
                confidence = min(confidence + 0.1, 1.0)
                
            if 'fractal' in problem.get('tags', []):
                confidence = min(confidence + 0.1, 1.0)
            
            # Large problems benefit from decomposition
            if 'grid_size' in problem:
                size = self._get_problem_size(problem)
                if size > 1000:
                    confidence = min(confidence + 0.05, 1.0)
            
            # Ensure confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))
            
            # Always return True for can_solve, but confidence varies
            return True, confidence
            
        except Exception as e:
            logger.debug(f"Error in can_solve analysis: {e}")
            # Default: medium confidence for unknown problems
            return True, 0.5

    def get_requirements(self) -> Dict[str, Any]:
        """
        Get requirements for this solver.
        
        Returns:
            Dictionary of requirements
        """
        return {
            'solver_type': 'recursive',
            'required_capabilities': ['decomposition', 'stitching'],
            'supported_problem_types': [
                'complex_waveguide',
                'multi_domain',
                'fractal_design',
                'large_scale',
                'hierarchical',
                'recursive'
            ],
            'memory_requirements': 'moderate',
            'computation_requirements': 'high',
            'max_recursion_depth': self.max_recursion_depth,
            'min_problem_complexity': self.min_problem_complexity,
            'version': self.version,
            'description': 'Recursive solver for fractal decomposition of complex problems',
            'priority': 8,
            'recursion_support': True
        }

    def analyze_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze problem for recursive decomposition suitability.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            Analysis results including complexity score
        """
        complexity = 3.0  # Base complexity
        
        # Analyze problem size
        if 'grid_size' in problem:
            size = problem['grid_size']
            if isinstance(size, tuple):
                complexity += min(sum(size) / 100, 5.0)
            elif isinstance(size, int):
                complexity += min(size / 50, 5.0)
        
        # Check for nonlinear components
        if problem.get('nonlinear', False):
            complexity += 2.0
            
        # Check for multiple domains
        if 'subdomains' in problem:
            complexity += len(problem['subdomains']) * 0.5
            
        # Boundary conditions increase complexity
        if 'boundary_conditions' in problem:
            bc_count = len(problem['boundary_conditions'])
            complexity += min(bc_count * 0.3, 2.0)
        
        # Source complexity
        if 'sources' in problem:
            complexity += min(len(problem['sources']) * 0.5, 2.0)
            
        # Material complexity
        if 'materials' in problem:
            material_count = len(problem['materials'])
            if material_count > 1:
                complexity += min((material_count - 1) * 0.4, 1.5)
        
        # Check for recursion hints
        if problem.get('requires_recursion', False):
            complexity += 2.0
            
        if 'recursive' in problem.get('tags', []):
            complexity += 1.5
            
        if 'fractal' in problem.get('tags', []):
            complexity += 2.0
        
        # Constrain complexity to 1-10 range
        complexity = max(1.0, min(complexity, 10.0))
        
        # Determine if decomposition is beneficial
        should_decompose = (
            complexity > self.min_problem_complexity and
            'grid_size' in problem and
            self._get_problem_size(problem) > self.min_subproblem_size
        )
        
        analysis = {
            'complexity': complexity,
            'should_decompose': should_decompose,
            'decomposition_type': 'recursive' if should_decompose else 'direct',
            'estimated_subproblems': max(2, int(complexity / 3)),
            'depth_required': min(3, int(complexity / 4)),
            'estimated_time': complexity * 0.1,  # Rough estimate in seconds
            'memory_footprint': 'high' if complexity > 7 else 'medium',
            'recursion_recommended': complexity > 6
        }
        
        return analysis

    def _get_problem_size(self, problem: Dict[str, Any]) -> int:
        """Extract problem size from problem dictionary."""
        if 'grid_size' in problem:
            size = problem['grid_size']
            if isinstance(size, tuple):
                return size[0] * size[1]
            elif isinstance(size, int):
                return size
        return 100  # Default size

    def _decompose_problem(self, problem: Dict[str, Any], depth: int) -> List[Dict[str, Any]]:
        """
        Decompose a problem into subproblems.
        
        Args:
            problem: Original problem
            depth: Current recursion depth
            
        Returns:
            List of subproblem dictionaries
        """
        self.decomposition_count += 1
        
        # Determine decomposition strategy
        if self.decomposition_strategy == "uniform":
            return self._uniform_decomposition(problem, depth)
        elif self.decomposition_strategy == "adaptive":
            return self._adaptive_decomposition(problem, depth)
        else:
            return self._quadtree_decomposition(problem, depth)

    def _uniform_decomposition(self, problem: Dict[str, Any], depth: int) -> List[Dict[str, Any]]:
        """Uniform grid decomposition."""
        subproblems = []
        
        if 'grid_size' in problem:
            grid_size = problem['grid_size']
            if isinstance(grid_size, tuple) and len(grid_size) == 2:
                rows, cols = grid_size
                
                # Split into quadrants
                half_rows = max(rows // 2, 1)
                half_cols = max(cols // 2, 1)
                
                subgrids = [
                    (0, half_rows, 0, half_cols),  # Top-left
                    (0, half_rows, half_cols, cols),  # Top-right
                    (half_rows, rows, 0, half_cols),  # Bottom-left
                    (half_rows, rows, half_cols, cols)  # Bottom-right
                ]
                
                for i, (r_start, r_end, c_start, c_end) in enumerate(subgrids):
                    subproblem = problem.copy()
                    subproblem['grid_size'] = (r_end - r_start, c_end - c_start)
                    subproblem['subdomain_id'] = f"sub_{depth}_{i}"
                    subproblem['parent_problem'] = problem.get('problem_id', 'root')
                    
                    # Mark as subproblem for stitching
                    subproblem['is_subproblem'] = True
                    subproblem['subproblem_index'] = i
                    subproblem['total_subproblems'] = 4
                    
                    # Adjust parameters for subdomain
                    if 'domain_bounds' in problem:
                        bounds = problem['domain_bounds']
                        if isinstance(bounds, dict) and 'x' in bounds and 'y' in bounds:
                            x_range = bounds['x'][1] - bounds['x'][0]
                            y_range = bounds['y'][1] - bounds['y'][0]
                            
                            x_start = bounds['x'][0] + (c_start / cols) * x_range
                            x_end = bounds['x'][0] + (c_end / cols) * x_range
                            y_start = bounds['y'][0] + (r_start / rows) * y_range
                            y_end = bounds['y'][0] + (r_end / rows) * y_range
                            
                            subproblem['domain_bounds'] = {
                                'x': (x_start, x_end),
                                'y': (y_start, y_end)
                            }
                    
                    # Add boundary information for stitching
                    subproblem['boundary_info'] = {
                        'parent_id': problem.get('problem_id', 'root'),
                        'position_in_parent': i,
                        'neighbors': self._get_neighbor_indices(i),
                        'boundary_type': 'internal'
                    }
                    
                    subproblems.append(subproblem)
        
        return subproblems if subproblems else [problem]

    def _get_neighbor_indices(self, position: int) -> List[int]:
        """Get neighbor indices for a quadrant position (0-3)."""
        neighbor_map = {
            0: [1, 2],  # Top-left neighbors: top-right, bottom-left
            1: [0, 3],  # Top-right neighbors: top-left, bottom-right
            2: [0, 3],  # Bottom-left neighbors: top-left, bottom-right
            3: [1, 2]   # Bottom-right neighbors: top-right, bottom-left
        }
        return neighbor_map.get(position, [])

    def _adaptive_decomposition(self, problem: Dict[str, Any], depth: int) -> List[Dict[str, Any]]:
        """Adaptive decomposition based on problem features."""
        # Start with uniform decomposition
        subproblems = self._uniform_decomposition(problem, depth)
        
        # Adjust based on problem complexity
        analysis = self.analyze_problem(problem)
        complexity = analysis['complexity']
        
        if complexity > 7 and depth < 2:
            # Further decompose complex problems at shallow depth
            further_decomposed = []
            for i, sub in enumerate(subproblems):
                if i == 0 or i == len(subproblems) - 1:  # First and last
                    sub_sub = self._uniform_decomposition(sub, depth + 1)
                    further_decomposed.extend(sub_sub)
                else:
                    further_decomposed.append(sub)
            return further_decomposed
        
        return subproblems

    def _quadtree_decomposition(self, problem: Dict[str, Any], depth: int) -> List[Dict[str, Any]]:
        """Quadtree-style decomposition."""
        subproblems = self._uniform_decomposition(problem, depth)
        
        # For deep recursion, use simpler decomposition
        if depth >= 2:
            # Return only 2 subproblems instead of 4
            return subproblems[:2]
        
        return subproblems

    def _stitch_solutions(self, solutions: List[FieldSolution], 
                         original_problem: Dict[str, Any]) -> FieldSolution:
        """
        Stitch together subproblem solutions.
        
        Args:
            solutions: List of FieldSolution objects
            original_problem: Original problem definition
            
        Returns:
            Stitched FieldSolution
        """
        if len(solutions) == 1:
            return solutions[0]
        
        # Use StitchingSolver for complex stitching
        stitching_problem = {
            'problem_type': 'stitching',
            'subdomain_solutions': solutions,
            'original_problem': original_problem,
            'stitching_method': 'hierarchical' if len(solutions) > 2 else 'direct',
            'overlap_region': 0.1,  # 10% overlap
            'problem_id': f'stitch_{id(solutions)}',
            'requires_stitching': True
        }
        
        # Create a solver manager without RecursiveSolver to avoid recursion
        local_manager = create_solver_manager()
        local_manager.solvers = {
            sid: solver for sid, solver in local_manager.solvers.items()
            if not isinstance(solver, RecursiveSolver)
        }
        
        try:
            result = local_manager.solve(stitching_problem)
            logger.info(f"Stitching successful: {len(solutions)} solutions merged")
            return result
        except Exception as e:
            logger.warning(f"Stitching failed: {e}. Falling back to simple merge.")
            return self._simple_merge(solutions)

    def _simple_merge(self, solutions: List[FieldSolution]) -> FieldSolution:
        """Simple merging of solutions (fallback)."""
        # Take the first solution and adjust metadata
        primary = solutions[0]
        
        # Create merged solution
        merged = FieldSolution(
            amplitude=primary.amplitude.copy(),
            phase=primary.phase.copy(),
            spatial_dim=primary.spatial_dim,
            grid_x=primary.grid_x.copy() if primary.grid_x is not None else None,
            grid_y=primary.grid_y.copy() if primary.grid_y is not None else None,
            wavelength=primary.wavelength,
            solver_used=f"RecursiveSolver_merged_{len(solutions)}",
            metadata={
                **primary.metadata,
                'merged_solutions': len(solutions),
                'merge_method': 'simple_average',
                'stitching_failed': True,
                'recursion_metadata': {
                    'solutions_merged': len(solutions),
                    'merge_timestamp': time.time()
                }
            }
        )
        
        return merged

    def _create_final_solution(self, stitched_solution: FieldSolution,
                              original_problem: Dict[str, Any],
                              execution_time: float) -> FieldSolution:
        """
        Create final solution with metadata.
        
        Args:
            stitched_solution: The stitched solution
            original_problem: Original problem
            execution_time: Total execution time
            
        Returns:
            Final FieldSolution with metadata
        """
        # Create final solution with metadata
        final_solution = FieldSolution(
            amplitude=stitched_solution.amplitude,
            phase=stitched_solution.phase,
            spatial_dim=stitched_solution.spatial_dim,
            grid_x=stitched_solution.grid_x,
            grid_y=stitched_solution.grid_y,
            wavelength=stitched_solution.wavelength,
            solver_used=f"{self.name}_v{self.version}",
            metadata={
                **stitched_solution.metadata,
                'recursion_depth': self.max_depth_reached,
                'decompositions': self.decomposition_count,
                'direct_solves': self.direct_solve_count,
                'execution_time': execution_time,
                'original_problem_id': original_problem.get('problem_id', 'unknown'),
                'solver_version': self.version,
                'fractal_levels': min(3, self.max_depth_reached),
                'recursion_metadata': self._get_recursion_metadata(original_problem),
                'performance_summary': self._get_performance_summary()
            }
        )
        
        return final_solution
    
    def _get_recursion_metadata(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recursion metadata."""
        tree_info = self.get_recursion_tree_info()
        
        return {
            'max_depth': self.max_depth_reached,
            'total_nodes': len(self.recursion_tree),
            'decomposition_strategy': self.decomposition_strategy,
            'problem_complexity': self.analyze_problem(problem).get('complexity', 0),
            'tree_structure': tree_info.get('tree_structure', {}),
            'performance_metrics': tree_info.get('performance', {})
        }
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary."""
        return {
            'max_depth': self.max_depth_reached,
            'total_decompositions': self.decomposition_count,
            'direct_solutions': self.direct_solve_count,
            'efficiency_ratio': (
                self.direct_solve_count / max(self.decomposition_count, 1)
            ),
            'recursion_efficiency': self._calculate_recursion_efficiency()
        }
    
    def _calculate_recursion_efficiency(self) -> float:
        """Calculate recursion efficiency metric."""
        if not self.recursion_tree:
            return 0.0
        
        total_nodes = len(self.recursion_tree)
        leaf_nodes = sum(1 for node in self.recursion_tree.values() if not node.children)
        
        if leaf_nodes == 0:
            return 0.0
        
        # Efficiency: ratio of leaf nodes to total nodes
        # Higher is better (more work done at leaves)
        return leaf_nodes / total_nodes

    def _solve_recursive(self, node_id: str) -> FieldSolution:
        """
        Recursive solving method.
        
        Args:
            node_id: ID of the node to solve
            
        Returns:
            Solution for this node and its subtree
        """
        if node_id in self._visited_nodes:
            logger.error(f"Cycle detected at node {node_id}")
            raise RuntimeError(f"Recursion cycle detected at node {node_id}")
        
        self._visited_nodes.add(node_id)
        
        try:
            node = self.recursion_tree[node_id]
            
            # Update max depth
            self.max_depth_reached = max(self.max_depth_reached, node.depth)
            
            # Check stopping conditions
            stop_conditions = [
                node.depth >= self.max_recursion_depth,
                node.complexity <= self.min_problem_complexity,
                self._get_problem_size(node.problem) <= self.min_subproblem_size,
                node.problem.get('is_subproblem', False) and node.depth >= 2
            ]
            
            if any(stop_conditions):
                logger.debug(f"Direct solve at depth {node.depth}, complexity {node.complexity:.1f}")
                return self._solve_directly(node)
            
            # Decompose and solve children
            if not node.children:
                logger.debug(f"Decomposing node {node_id} at depth {node.depth}")
                subproblems = self._decompose_problem(node.problem, node.depth + 1)
                
                child_solutions = []
                for i, subproblem in enumerate(subproblems):
                    child_id = f"{node_id}_child{i}"
                    
                    # Create child node
                    child_analysis = self.analyze_problem(subproblem)
                    child_node = RecursionNode(
                        node_id=child_id,
                        problem=subproblem,
                        depth=node.depth + 1,
                        complexity=child_analysis['complexity'],
                        parent=node_id
                    )
                    
                    self.recursion_tree[child_id] = child_node
                    node.children.append(child_id)
                    
                    # Solve child recursively
                    child_solution = self._solve_recursive(child_id)
                    child_solutions.append(child_solution)
                
                # Stitch child solutions
                stitched = self._stitch_solutions(child_solutions, node.problem)
                node.solution = stitched
                node.solved = True
                
                return stitched
            else:
                # Node already has children, solve them
                child_solutions = []
                for child_id in node.children:
                    child_solution = self._solve_recursive(child_id)
                    child_solutions.append(child_solution)
                
                # Stitch existing children
                stitched = self._stitch_solutions(child_solutions, node.problem)
                node.solution = stitched
                node.solved = True
                
                return stitched
                
        finally:
            self._visited_nodes.remove(node_id)

    def _solve_directly(self, node: RecursionNode) -> FieldSolution:
        """
        Solve a leaf node directly (no further decomposition).
        
        Args:
            node: The node to solve
            
        Returns:
            Direct solution
        """
        self.direct_solve_count += 1
        
        # Create local manager without RecursiveSolver
        local_manager = create_solver_manager()
        
        # Filter out RecursiveSolver to prevent infinite recursion
        filtered_solvers = {}
        for solver_id, solver in local_manager.solvers.items():
            if not isinstance(solver, RecursiveSolver):
                filtered_solvers[solver_id] = solver
        
        if not filtered_solvers:
            logger.warning("No non-recursive solvers available. Using fallback.")
            return self._create_fallback_solution(node.problem)
        
        local_manager.solvers = filtered_solvers
        
        try:
            # Mark problem as leaf for tracking
            leaf_problem = node.problem.copy()
            leaf_problem['is_leaf_node'] = True
            leaf_problem['recursion_depth'] = node.depth
            
            solution = local_manager.solve(leaf_problem)
            node.solution = solution
            node.solved = True
            
            # Add recursion metadata to solution
            if solution.metadata is None:
                solution.metadata = {}
            
            solution.metadata.update({
                'recursion_leaf': True,
                'leaf_depth': node.depth,
                'leaf_complexity': node.complexity
            })
            
            return solution
        except Exception as e:
            logger.error(f"Direct solve failed for node {node.node_id}: {e}")
            return self._create_fallback_solution(node.problem)

    def _create_fallback_solution(self, problem: Dict[str, Any]) -> FieldSolution:
        """Create a fallback solution when all else fails."""
        logger.warning(f"Creating fallback solution for problem: {problem.get('problem_id', 'unknown')}")
        
        # Create simple solution
        if 'grid_size' in problem:
            grid_size = problem['grid_size']
            if isinstance(grid_size, tuple):
                rows, cols = grid_size
                amplitude = np.ones((rows, cols))
                phase = np.zeros((rows, cols))
                spatial_dim = 2
            else:
                amplitude = np.ones(grid_size)
                phase = np.zeros(grid_size)
                spatial_dim = 1
        else:
            amplitude = np.ones((10, 10))
            phase = np.zeros((10, 10))
            spatial_dim = 2
        
        return FieldSolution(
            amplitude=amplitude,
            phase=phase,
            spatial_dim=spatial_dim,
            solver_used=f"{self.name}_fallback",
            metadata={
                'fallback': True,
                'reason': 'All solvers failed',
                'problem_id': problem.get('problem_id', 'unknown'),
                'recursion_fallback': True
            }
        )

    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Main solve method implementing recursive decomposition.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            FieldSolution from recursive solving
        """
        start_time = time.time()
        
        # Reset state for new problem
        self.recursion_tree.clear()
        self._visited_nodes.clear()
        self.decomposition_count = 0
        self.direct_solve_count = 0
        self.max_depth_reached = 0
        
        try:
            # Analyze problem
            analysis = self.analyze_problem(problem)
            logger.info(f"Problem analysis: complexity={analysis['complexity']:.1f}, "
                       f"decompose={analysis['should_decompose']}")
            
            # Create root node
            root_id = "root"
            root_node = RecursionNode(
                node_id=root_id,
                problem=problem,
                depth=0,
                complexity=analysis['complexity']
            )
            self.recursion_tree[root_id] = root_node
            
            # Recursive solving
            final_solution = self._solve_recursive(root_id)
            
            # Add recursion metadata
            execution_time = time.time() - start_time
            
            final_with_metadata = self._create_final_solution(
                final_solution, problem, execution_time
            )
            
            logger.info(f"Recursive solving completed: "
                       f"depth={self.max_depth_reached}, "
                       f"decompositions={self.decomposition_count}, "
                       f"direct={self.direct_solve_count}, "
                       f"time={execution_time:.3f}s")
            
            return final_with_metadata
            
        except Exception as e:
            logger.error(f"Recursive solving failed: {e}")
            
            # Provide fallback solution
            execution_time = time.time() - start_time
            fallback = self._create_fallback_solution(problem)
            
            fallback.metadata.update({
                'error': str(e),
                'execution_time': execution_time,
                'partial_depth': self.max_depth_reached,
                'recursion_failed': True
            })
            
            return fallback

    def get_recursion_tree_info(self) -> Dict[str, Any]:
        """
        Get information about the recursion tree.
        
        Returns:
            Dictionary with tree statistics
        """
        if not self.recursion_tree:
            return {'empty': True}
        
        total_nodes = len(self.recursion_tree)
        solved_nodes = sum(1 for node in self.recursion_tree.values() if node.solved)
        max_depth = max((node.depth for node in self.recursion_tree.values()), default=0)
        
        # Count nodes by depth
        nodes_by_depth = {}
        leaf_nodes = 0
        for node in self.recursion_tree.values():
            nodes_by_depth[node.depth] = nodes_by_depth.get(node.depth, 0) + 1
            if not node.children:
                leaf_nodes += 1
        
        # Calculate average complexity
        avg_complexity = sum(n.complexity for n in self.recursion_tree.values()) / total_nodes
        
        return {
            'total_nodes': total_nodes,
            'solved_nodes': solved_nodes,
            'leaf_nodes': leaf_nodes,
            'max_depth': max_depth,
            'nodes_by_depth': nodes_by_depth,
            'decomposition_count': self.decomposition_count,
            'direct_solve_count': self.direct_solve_count,
            'performance': {
                'max_depth_reached': self.max_depth_reached,
                'avg_complexity': avg_complexity,
                'efficiency': self.direct_solve_count / max(self.decomposition_count, 1),
                'leaf_ratio': leaf_nodes / total_nodes if total_nodes > 0 else 0
            },
            'tree_structure': {
                node_id: {
                    'depth': node.depth,
                    'complexity': node.complexity,
                    'solved': node.solved,
                    'children': node.children,
                    'parent': node.parent,
                    'is_leaf': not node.children
                }
                for node_id, node in self.recursion_tree.items()
            }
        }


# Need numpy for fallback solutions
import numpy as np
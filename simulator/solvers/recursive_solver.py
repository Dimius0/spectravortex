"""
Recursive Solver for Fractal Computation Architecture.
Implements recursive problem decomposition and hierarchical stitching.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from .solver import Solver
from .core.data_interface import FieldSolution
from .core.solver_manager import SolverManager, create_solver_manager

logger = logging.getLogger(__name__)

@dataclass
class RecursionNode:
    """Node in the recursive decomposition tree."""
    node_id: str
    problem: Dict[str, Any]
    depth: int
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    solution: Optional[FieldSolution] = None
    solver_used: Optional[str] = None
    computation_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

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
        super().__init__()
        self.name = name
        self.version = version
        self.max_recursion_depth = 4
        self.min_problem_complexity = 5  # Scale from 1-10
        self.decomposition_strategy = "adaptive"
        self.recursion_tree: Dict[str, RecursionNode] = {}
        
        # Create internal solver manager for subproblems
        self.solver_manager = create_solver_manager(enable_auto_selection=True)
        
        logger.info(f"Initialized {name} v{version}")
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get solver requirements and capabilities."""
        return {
            "physical_models": ["linear", "wave_propagation", "nonlinear"],
            "max_dimensions": 3,
            "recursion_depth": self.max_recursion_depth,
            "decomposition_strategies": ["adaptive", "spatial", "physical"],
            "supports_topology_analysis": True,
            "supports_stitching": True,
            "fractal_capable": True,
        }
    
    def can_solve(self, problem: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if this solver can handle the problem recursively.
        
        Args:
            problem: Problem description dictionary
        
        Returns:
            (can_solve, reason)
        """
        # Check if problem has complexity that warrants recursion
        complexity = self._estimate_recursion_complexity(problem)
        
        if complexity < self.min_problem_complexity:
            return False, f"Problem complexity ({complexity}) too low for recursion"
        
        # Check if problem can be decomposed
        can_decompose = self._can_decompose_problem(problem)
        if not can_decompose:
            return False, "Problem cannot be decomposed"
        
        return True, f"Suitable for recursive decomposition (complexity: {complexity})"
    
    def estimate_computation_cost(self, problem: Dict[str, Any]) -> Dict[str, float]:
        """Estimate computation cost for recursive solving."""
        complexity = self._estimate_recursion_complexity(problem)
        estimated_depth = min(self.max_recursion_depth, complexity // 3)
        
        # Exponential growth with depth
        estimated_leaf_nodes = 2 ** estimated_depth
        
        return {
            "time_seconds": 0.5 * estimated_leaf_nodes,
            "memory_mb": 50 * estimated_leaf_nodes,
            "complexity": float(complexity),
            "estimated_depth": float(estimated_depth),
            "estimated_nodes": float(estimated_leaf_nodes),
            "recursion_complexity": "high" if estimated_depth > 2 else "medium",
        }
    
    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Solve a problem using recursive decomposition.
        
        Args:
            problem: Problem description dictionary
        
        Returns:
            FieldSolution with results and recursion metadata
        """
        start_time = time.time()
        logger.info(f"{self.name} starting recursive solve for: {problem.get('name', 'unnamed')}")
        
        # Reset recursion tree
        self.recursion_tree = {}
        
        # Create root node
        root_node = RecursionNode(
            node_id="root",
            problem=problem.copy(),
            depth=0,
            parent_id=None,
        )
        self.recursion_tree["root"] = root_node
        
        # Start recursive solution
        logger.info(f"Starting recursion with max depth: {self.max_recursion_depth}")
        final_solution = self._solve_recursive("root")
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Add recursion metadata to solution
        final_solution.metadata["recursion"] = {
            "solver_used": self.name,
            "solver_version": self.version,
            "total_computation_time": total_time,
            "recursion_tree": self._serialize_recursion_tree(),
            "total_nodes": len(self.recursion_tree),
            "max_depth": self._get_max_depth(),
            "decomposition_strategy": self.decomposition_strategy,
            "fractal_pattern": self._analyze_fractal_pattern(),
        }
        
        logger.info(
            f"{self.name} completed recursion in {total_time:.3f}s, "
            f"nodes: {len(self.recursion_tree)}, depth: {self._get_max_depth()}"
        )
        
        return final_solution
    
    def _solve_recursive(self, node_id: str) -> FieldSolution:
        """
        Recursively solve a problem node.
        
        Args:
            node_id: ID of the node to solve
        
        Returns:
            FieldSolution for this node
        """
        node = self.recursion_tree[node_id]
        
        # Check recursion depth limit
        if node.depth >= self.max_recursion_depth:
            logger.debug(f"Depth limit reached at node {node_id}, solving directly")
            return self._solve_directly(node)
        
        # Decide: decompose or solve directly
        should_decompose = self._should_decompose(node)
        
        if should_decompose:
            # Decompose and solve children recursively
            return self._solve_via_decomposition(node)
        else:
            # Solve this node directly
            return self._solve_directly(node)
    
    def _solve_directly(self, node: RecursionNode) -> FieldSolution:
        """Solve a node directly using the solver manager."""
        start_time = time.time()
        
        # Use solver manager to solve this problem
        solution = self.solver_manager.solve(node.problem)
        
        # Update node information
        node.solution = solution
        node.solver_used = solution.metadata.get("solver_manager", {}).get("selected_solver", "unknown")
        node.computation_time = time.time() - start_time
        node.metadata["solved_directly"] = True
        node.metadata["selected_solver"] = node.solver_used
        
        logger.debug(f"Direct solve for node {node.node_id}: {node.solver_used} in {node.computation_time:.3f}s")
        
        return solution
    
    def _solve_via_decomposition(self, node: RecursionNode) -> FieldSolution:
        """Solve by decomposing into subproblems and stitching results."""
        start_time = time.time()
        
        # Decompose the problem
        decomposition_strategy = self._choose_decomposition_strategy(node)
        problem_parts = self.solver_manager.decompose_problem(
            node.problem, 
            decomposition_strategy=decomposition_strategy
        )
        
        if len(problem_parts) < 2:
            logger.warning(f"Decomposition produced only {len(problem_parts)} parts, solving directly")
            return self._solve_directly(node)
        
        # Create child nodes and solve them recursively
        child_solutions = []
        for i, part in enumerate(problem_parts):
            child_id = f"{node.node_id}_child{i}"
            
            child_node = RecursionNode(
                node_id=child_id,
                problem=part.problem_description,
                depth=node.depth + 1,
                parent_id=node.node_id,
            )
            self.recursion_tree[child_id] = child_node
            node.children.append(child_id)
            
            # Recursive solve
            child_solution = self._solve_recursive(child_id)
            child_solutions.append(child_solution)
        
        # Prepare stitching problem
        stitching_problem = {
            "name": f"stitch_{node.node_id}",
            "subdomain_solutions": child_solutions,
            "domain_layout": self._create_stitching_layout(node, problem_parts),
            "stitching_method": "weighted_overlap",
            "metadata": {
                "parent_node": node.node_id,
                "decomposition_strategy": decomposition_strategy,
                "num_children": len(child_solutions),
            }
        }
        
        # Stitch the solutions together
        try:
            from .stitching_solver import StitchingSolver
            stitching_solver = StitchingSolver()
            stitched_solution = stitching_solver.solve(stitching_problem)
            
            # Update node information
            node.solution = stitched_solution
            node.solver_used = "StitchingSolver"
            node.computation_time = time.time() - start_time
            node.metadata["solved_via_decomposition"] = True
            node.metadata["decomposition_strategy"] = decomposition_strategy
            node.metadata["num_children"] = len(child_solutions)
            node.metadata["stitching_method"] = "weighted_overlap"
            
            logger.debug(
                f"Decomposition solve for node {node.node_id}: "
                f"{len(child_solutions)} children stitched in {node.computation_time:.3f}s"
            )
            
            return stitched_solution
            
        except ImportError as e:
            logger.error(f"StitchingSolver not available: {e}")
            # Fall back to direct solution
            return self._solve_directly(node)
    
    def _estimate_recursion_complexity(self, problem: Dict[str, Any]) -> float:
        """Estimate complexity for recursion decision."""
        complexity = 1.0
        
        # Factor 1: Domain size
        domain = problem.get("domain", {})
        if domain.get("type") == "2d":
            width = domain.get("width", 1e-6)
            height = domain.get("height", 1e-6)
            grid_size = domain.get("grid_size", 0.1e-6)
            
            if width > 0 and height > 0 and grid_size > 0:
                nx = width / grid_size
                ny = height / grid_size
                complexity += (nx * ny) / 1000
        
        # Factor 2: Physics complexity
        physics = problem.get("physics", [])
        if "nonlinear" in physics:
            complexity += 3.0
        if "interference" in physics:
            complexity += 2.0
        if any("vortex" in p for p in physics):
            complexity += 4.0
        
        # Factor 3: Number of components
        components = problem.get("components", [])
        complexity += len(components) * 0.5
        
        # Factor 4: Topological complexity
        if problem.get("parameters", {}).get("orbital_angular_momentum"):
            complexity += 5.0
        
        return min(complexity, 10.0)  # Cap at 10
    
    def _can_decompose_problem(self, problem: Dict[str, Any]) -> bool:
        """Check if a problem can be decomposed."""
        domain = problem.get("domain", {})
        
        # Can decompose 2D and 3D problems spatially
        if domain.get("type") in ["2d", "3d"]:
            return True
        
        # Can decompose if multiple physical models
        physics = problem.get("physics", [])
        if len(physics) > 1:
            return True
        
        # Can decompose if explicitly marked for decomposition
        if problem.get("decomposition_strategy"):
            return True
        
        return False
    
    def _should_decompose(self, node: RecursionNode) -> bool:
        """Decide whether to decompose this node."""
        if node.depth >= self.max_recursion_depth:
            return False
        
        complexity = self._estimate_recursion_complexity(node.problem)
        
        # Higher complexity -> more likely to decompose
        decompose_threshold = self.min_problem_complexity + node.depth * 0.5
        
        return complexity >= decompose_threshold
    
    def _choose_decomposition_strategy(self, node: RecursionNode) -> str:
        """Choose the best decomposition strategy for this node."""
        domain = node.problem.get("domain", {})
        
        if domain.get("type") == "2d":
            return "spatial"
        elif node.problem.get("physics", []):
            # Multiple physics models -> physical decomposition
            physics = node.problem.get("physics", [])
            if len(physics) > 1:
                return "physical"
        
        return self.decomposition_strategy
    
    def _create_stitching_layout(self, node: RecursionNode, parts: List) -> Dict[str, Any]:
        """Create layout information for stitching."""
        layout = {}
        
        for i, part in enumerate(parts):
            domain_id = f"domain_{i}"
            
            # Try to get bounds from part metadata
            if hasattr(part, 'problem_description'):
                bounds = part.problem_description.get("domain", {})
            else:
                # Default bounds
                bounds = {"x_min": i * 10, "x_max": (i + 1) * 10, "y_min": 0, "y_max": 10}
            
            layout[domain_id] = bounds
        
        return layout
    
    def _serialize_recursion_tree(self) -> Dict[str, Any]:
        """Serialize recursion tree for metadata."""
        serialized = {}
        
        for node_id, node in self.recursion_tree.items():
            serialized[node_id] = {
                "depth": node.depth,
                "parent": node.parent_id,
                "children": node.children,
                "solver_used": node.solver_used,
                "computation_time": node.computation_time,
                "metadata": node.metadata,
            }
        
        return serialized
    
    def _get_max_depth(self) -> int:
        """Get maximum depth of recursion tree."""
        if not self.recursion_tree:
            return 0
        
        return max(node.depth for node in self.recursion_tree.values())
    
    def _analyze_fractal_pattern(self) -> Dict[str, Any]:
        """Analyze fractal patterns in the recursion tree."""
        if not self.recursion_tree:
            return {"pattern": "none", "self_similarity": 0.0}
        
        # Calculate branching factor statistics
        branching_factors = []
        for node in self.recursion_tree.values():
            if node.children:
                branching_factors.append(len(node.children))
        
        if not branching_factors:
            return {"pattern": "linear", "self_similarity": 0.0}
        
        avg_branching = sum(branching_factors) / len(branching_factors)
        
        # Check for self-similarity (fractal pattern)
        variance = sum((bf - avg_branching) ** 2 for bf in branching_factors) / len(branching_factors)
        
        # Low variance suggests fractal pattern (self-similar branching)
        is_fractal = variance < 1.0 and avg_branching > 1.5
        
        return {
            "pattern": "fractal" if is_fractal else "irregular",
            "self_similarity": 1.0 / (1.0 + variance),
            "avg_branching_factor": avg_branching,
            "max_depth": self._get_max_depth(),
        }

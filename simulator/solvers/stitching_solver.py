"""
Stitching Solver for Hybrid Architecture.
Combines multiple partial solutions into a unified field with boundary analysis.
"""

import logging
import numpy as np
import time
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

from simulator.core.solver import Solver
from simulator.core.data_interface import FieldSolution
from simulator.core.topological_analysis import TopologicalFeature

logger = logging.getLogger(__name__)


@dataclass
class SubdomainSolution:
    """Container for a solution in a specific subdomain."""
    solution: FieldSolution
    domain_bounds: Dict[str, float]  # x_min, x_max, y_min, y_max, etc.
    overlap_region: Dict[str, Any] = field(default_factory=dict)
    solver_used: str = "unknown"


@dataclass
class StitchingBoundary:
    """Data for a boundary between two subdomains."""
    domain_a_id: str
    domain_b_id: str
    boundary_type: str  # 'horizontal', 'vertical', 'diagonal'
    overlap_indices_a: List[Tuple[int, int]]
    overlap_indices_b: List[Tuple[int, int]]
    phase_discontinuity: Optional[float] = None
    amplitude_ratio: float = 1.0


class StitchingSolver(Solver):
    """
    Solver that stitches together multiple partial solutions.
    
    This is the core of Phase 3: enabling true hybrid computations
    where different subdomains are solved by different solvers.
    """

    def __init__(self, name: str = "StitchingSolver", version: str = "1.0"):
        super().__init__(name=name)

        self.version = version
        self.stitching_method = "weighted_overlap"  # Default method
        self.overlap_width = 3  # Number of grid points for overlap region
        self.min_confidence = 0.7  # Minimum confidence for stitching

        logger.info(f"Initialized {name} v{version}")

    def can_solve(self, problem: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Check if this solver can stitch the given problem.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            Tuple of (can_solve, confidence)
        """
        try:
            # Проверяем, является ли это задачей сшивания
            is_stitching_problem = (
                problem.get('problem_type') == 'stitching' or
                'subdomain_solutions' in problem or
                ('subdomains' in problem and len(problem.get('subdomains', [])) > 1)
            )
            
            if not is_stitching_problem:
                return False, 0.0
            
            # Базовая уверенность
            confidence = 0.7
            
            # Безопасная обработка grid_size
            if 'grid_size' in problem:
                grid_size = problem['grid_size']
                if isinstance(grid_size, tuple):
                    # Безопасный расчет - избегаем умножения кортежа
                    try:
                        if len(grid_size) == 2:
                            total_cells = grid_size[0] * grid_size[1]
                            if total_cells > 1000:
                                confidence += 0.1
                    except (TypeError, IndexError):
                        pass  # Игнорируем ошибки расчета
                elif isinstance(grid_size, (int, float)):
                    if grid_size > 1000:
                        confidence += 0.1
            
            # Дополнительные факторы уверенности
            if problem.get('requires_stitching', False):
                confidence += 0.2
            
            if 'subdomain_solutions' in problem:
                solutions = problem['subdomain_solutions']
                if hasattr(solutions, '__len__'):
                    confidence += min(0.2, len(solutions) * 0.05)
            
            # Ограничиваем confidence
            confidence = max(0.0, min(1.0, confidence))
            
            return True, confidence
            
        except Exception as e:
            # В случае ошибки возвращаем низкую уверенность
            logger.debug(f"Error in StitchingSolver.can_solve: {e}")
            return True, 0.3  # Минимальная уверенность для продолжения

    def get_requirements(self) -> Dict[str, Any]:
        """Get solver requirements and capabilities."""
        return {
            "physical_models": ["linear", "wave_propagation"],
            "max_dimensions": 3,
            "stitching_methods": ["weighted_overlap", "phase_correction", "fourier"],
            "supported_boundaries": ["horizontal", "vertical", "periodic"],
            "solver_type": "stitching",
            "priority": 5,
            "recursion_support": False
        }

    def estimate_computation_cost(self, problem: Dict[str, Any]) -> Dict[str, float]:
        """Estimate computation cost for stitching."""
        solutions = problem.get("subdomain_solutions", [])
        n_solutions = len(solutions)

        # Simple heuristic: cost grows with number of boundaries
        n_boundaries = max(0, n_solutions - 1)

        return {
            "time_seconds": 0.1 * n_boundaries + 0.5,
            "memory_mb": 10 * n_solutions,
            "complexity": float(n_boundaries),
            "stitching_complexity": "low" if n_solutions <= 4 else "medium",
        }

    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Stitch multiple subdomain solutions into a unified field.
        
        Args:
            problem: Dictionary containing:
                - subdomain_solutions: List of FieldSolution objects
                - domain_layout: Information about how subdomains are arranged
                - stitching_method: Optional, method to use
                
        Returns:
            Unified FieldSolution
        """
        start_time = time.time()
        logger.info(
            f"{self.name} starting stitching of "
            f"{len(problem.get('subdomain_solutions', []))} solutions"
        )

        # Extract parameters
        solutions = problem.get("subdomain_solutions", [])
        domain_layout = problem.get("domain_layout", {})
        method = problem.get("stitching_method", self.stitching_method)

        if len(solutions) < 2:
            raise ValueError("Need at least 2 solutions to stitch")

        # Prepare subdomain data
        subdomains = self._prepare_subdomains(solutions, domain_layout)

        # Detect boundaries between subdomains
        boundaries = self._detect_boundaries(subdomains, domain_layout)

        # Choose stitching method
        if method == "weighted_overlap":
            stitched_field = self._stitch_weighted_overlap(subdomains, boundaries)
        elif method == "phase_correction":
            stitched_field = self._stitch_with_phase_correction(subdomains, boundaries)
        else:
            logger.warning(f"Unknown method {method}, using weighted_overlap")
            stitched_field = self._stitch_weighted_overlap(subdomains, boundaries)

        # Analyze the stitched result
        topology_features = self._analyze_stitched_topology(
            stitched_field, boundaries
        )

        # Create the final solution
        elapsed = time.time() - start_time
        result = self._create_final_solution(
            stitched_field,
            subdomains,
            boundaries,
            topology_features,
            elapsed
        )

        logger.info(f"{self.name} completed stitching in {elapsed:.3f}s")
        return result

    def _prepare_subdomains(
        self,
        solutions: List[FieldSolution],
        layout: Dict[str, Any]
    ) -> List[SubdomainSolution]:
        """Prepare subdomain solutions for stitching."""
        subdomains = []

        for i, solution in enumerate(solutions):
            # Extract domain bounds from metadata or layout
            bounds_key = f"domain_{i}"
            if bounds_key in layout:
                bounds = layout[bounds_key]
            elif hasattr(solution, 'metadata') and 'domain_bounds' in solution.metadata:
                bounds = solution.metadata['domain_bounds']
            else:
                # Default bounds based on array shape
                shape = solution.amplitude.shape
                bounds = {
                    'x_min': 0,
                    'x_max': shape[1] if len(shape) > 1 else shape[0],
                    'y_min': 0,
                    'y_max': shape[0] if len(shape) > 1 else 1,
                }

            # Get solver info
            solver_used = "unknown"
            if hasattr(solution, 'metadata') and 'solver_used' in solution.metadata:
                solver_used = solution.metadata['solver_used']
            elif 'solver_manager' in getattr(solution, 'metadata', {}):
                solver_used = solution.metadata['solver_manager'].get(
                    'selected_solver', 'unknown'
                )

            subdomain = SubdomainSolution(
                solution=solution,
                domain_bounds=bounds,
                solver_used=solver_used,
            )
            subdomains.append(subdomain)

        return subdomains

    def _detect_boundaries(
        self,
        subdomains: List[SubdomainSolution],
        layout: Dict[str, Any]
    ) -> List[StitchingBoundary]:
        """Detect boundaries between adjacent subdomains."""
        boundaries = []
        n_domains = len(subdomains)

        # Simple 1D or 2D grid detection (can be extended)
        for i in range(n_domains):
            for j in range(i + 1, n_domains):
                bounds_i = subdomains[i].domain_bounds
                bounds_j = subdomains[j].domain_bounds

                # Check for adjacency
                adjacency, boundary_type = self._check_adjacency(bounds_i, bounds_j)

                if adjacency:
                    # Calculate overlap region
                    overlap = self._calculate_overlap(bounds_i, bounds_j, boundary_type)

                    boundary = StitchingBoundary(
                        domain_a_id=f"domain_{i}",
                        domain_b_id=f"domain_{j}",
                        boundary_type=boundary_type,
                        overlap_indices_a=overlap.get('indices_a', []),
                        overlap_indices_b=overlap.get('indices_b', []),
                    )
                    boundaries.append(boundary)

        logger.debug(f"Detected {len(boundaries)} boundaries between subdomains")
        return boundaries

    def _check_adjacency(
        self,
        bounds_a: Dict[str, float],
        bounds_b: Dict[str, float]
    ) -> Tuple[bool, Optional[str]]:
        """Check if two domains are adjacent and determine boundary type."""
        tolerance = 1e-9

        # Check for vertical boundary (shared x range, adjacent y)
        if (abs(bounds_a['x_min'] - bounds_b['x_min']) < tolerance and
            abs(bounds_a['x_max'] - bounds_b['x_max']) < tolerance):
            if abs(bounds_a['y_max'] - bounds_b['y_min']) < tolerance:
                return True, "vertical"
            elif abs(bounds_b['y_max'] - bounds_a['y_min']) < tolerance:
                return True, "vertical"

        # Check for horizontal boundary (shared y range, adjacent x)
        if (abs(bounds_a['y_min'] - bounds_b['y_min']) < tolerance and
            abs(bounds_a['y_max'] - bounds_b['y_max']) < tolerance):
            if abs(bounds_a['x_max'] - bounds_b['x_min']) < tolerance:
                return True, "horizontal"
            elif abs(bounds_b['x_max'] - bounds_a['x_min']) < tolerance:
                return True, "horizontal"

        return False, None

    def _calculate_overlap(
        self,
        bounds_a: Dict[str, float],
        bounds_b: Dict[str, float],
        boundary_type: str
    ) -> Dict[str, Any]:
        """Calculate overlap region between two domains."""
        overlap = {
            'indices_a': [],
            'indices_b': [],
            'width': self.overlap_width,
        }

        # Simplified: create synthetic overlap indices
        # In real implementation, this would use actual grid coordinates
        if boundary_type == "horizontal":
            # Overlap in x-direction at boundary
            for k in range(self.overlap_width):
                overlap['indices_a'].append((k, 0))  # Last rows of domain A
                overlap['indices_b'].append((k, 0))  # First rows of domain B
        elif boundary_type == "vertical":
            # Overlap in y-direction at boundary
            for k in range(self.overlap_width):
                overlap['indices_a'].append((0, k))  # Last columns of domain A
                overlap['indices_b'].append((0, k))  # First columns of domain B

        return overlap

    def _stitch_weighted_overlap(
        self,
        subdomains: List[SubdomainSolution],
        boundaries: List[StitchingBoundary]
    ) -> Dict[str, Any]:
        """
        Stitch using weighted average in overlap regions.
        
        Returns:
            Dictionary with stitched amplitude and phase arrays
        """
        # For now, implement a simplified version
        # In full implementation, this would merge actual fields

        # Get the combined domain size
        combined_shape = self._get_combined_shape(subdomains)

        # Create empty arrays for the combined field
        amplitude = np.zeros(combined_shape)
        phase = np.zeros(combined_shape)

        # Simple stitching: just place solutions in their domains
        # (proper weighted overlap would be more complex)
        for i, subdomain in enumerate(subdomains):
            sol = subdomain.solution
            bounds = subdomain.domain_bounds

            # Calculate slice indices
            x_start = int(bounds.get('x_min', 0))
            x_end = int(bounds.get('x_max', sol.amplitude.shape[1]))
            y_start = int(bounds.get('y_min', 0))
            y_end = int(bounds.get('y_max', sol.amplitude.shape[0]))

            # Ensure we don't exceed array bounds
            x_end = min(x_end, combined_shape[1])
            y_end = min(y_end, combined_shape[0])

            # Copy the subdomain solution
            if (y_end > y_start and x_end > x_start and
                sol.amplitude.shape[0] >= (y_end - y_start) and
                sol.amplitude.shape[1] >= (x_end - x_start)):

                amp_slice = sol.amplitude[
                    :(y_end - y_start),
                    :(x_end - x_start)
                ]
                phase_slice = sol.phase[
                    :(y_end - y_start),
                    :(x_end - x_start)
                ]

                amplitude[y_start:y_end, x_start:x_end] = amp_slice
                phase[y_start:y_end, x_start:x_end] = phase_slice

        return {
            'amplitude': amplitude,
            'phase': phase,
            'shape': combined_shape,
            'method': 'weighted_overlap',
        }

    def _stitch_with_phase_correction(
        self,
        subdomains: List[SubdomainSolution],
        boundaries: List[StitchingBoundary]
    ) -> Dict[str, Any]:
        """
        Stitch with phase correction to minimize discontinuities.
        """
        # Placeholder for phase-corrected stitching
        # This would adjust phases at boundaries for continuity

        result = self._stitch_weighted_overlap(subdomains, boundaries)
        result['method'] = 'phase_correction'
        result['phase_correction_applied'] = False  # Not implemented yet

        return result

    def _get_combined_shape(self, subdomains: List[SubdomainSolution]) -> Tuple[int, int]:
        """Calculate the shape of the combined domain."""
        max_x = 0
        max_y = 0

        for subdomain in subdomains:
            bounds = subdomain.domain_bounds
            sol_shape = subdomain.solution.amplitude.shape

            domain_x = int(bounds.get('x_max', sol_shape[1]))
            domain_y = int(bounds.get('y_max', sol_shape[0]))

            max_x = max(max_x, domain_x)
            max_y = max(max_y, domain_y)

        return (max_y, max_x)

    def _analyze_stitched_topology(
        self,
        stitched_field: Dict[str, Any],
        boundaries: List[StitchingBoundary]
    ) -> List[TopologicalFeature]:
        """
        Analyze topological features of the stitched field.
        
        This is where we connect stitching to topological protection.
        """
        features = []

        # Note: stitched_field['amplitude'] and stitched_field['phase'] 
        # would be used in a full implementation for analyzing field continuity

        # Simple feature detection (can be enhanced)
        # Look for phase singularities at boundary regions
        for boundary in boundaries:
            # Check for phase jumps at boundaries
            if boundary.overlap_indices_a and boundary.overlap_indices_b:
                # This is a placeholder - real implementation would analyze
                # phase continuity across boundaries using the actual field data
                feature = TopologicalFeature(
                    feature_type='boundary_interface',
                    location=(0.0, 0.0),  # Would be actual position
                    magnitude=1.0,
                    metadata={
                        'boundary_type': boundary.boundary_type,
                        'domains': [boundary.domain_a_id, boundary.domain_b_id],
                        'analysis': 'stitching_interface',
                    }
                )
                features.append(feature)

        logger.debug(f"Found {len(features)} topological features in stitched field")
        return features

    def _create_final_solution(
        self,
        stitched_field: Dict[str, Any],
        subdomains: List[SubdomainSolution],
        boundaries: List[StitchingBoundary],
        topology_features: List[TopologicalFeature],
        elapsed_time: float
    ) -> FieldSolution:
        """Create the final FieldSolution with stitching metadata."""
        # Create the solution object
        solution = FieldSolution(
            amplitude=stitched_field['amplitude'],
            phase=stitched_field['phase'],
            spatial_dim=stitched_field['amplitude'].ndim
        )

        # Add comprehensive metadata
        solution.metadata = {
            'solver_used': self.name,
            'solver_version': self.version,
            'computation_time': elapsed_time,
            'stitching': {
                'method': stitched_field.get('method', 'unknown'),
                'num_subdomains': len(subdomains),
                'num_boundaries': len(boundaries),
                'overlap_width': self.overlap_width,
                'subdomain_solvers': [s.solver_used for s in subdomains],
            },
            'topology': {
                'feature_count': len(topology_features),
                'analysis_type': 'stitching_boundary',
            },
            'field_properties': {
                'shape': stitched_field['amplitude'].shape,
                'amplitude_range': (
                    float(np.min(stitched_field['amplitude'])),
                    float(np.max(stitched_field['amplitude'])),
                ),
                'phase_range': (
                    float(np.min(stitched_field['phase'])),
                    float(np.max(stitched_field['phase'])),
                ),
            },
        }

        return solution

    def _get_domain_id(self, index: int) -> str:
        """Generate a domain ID from index."""
        return f"domain_{index}"
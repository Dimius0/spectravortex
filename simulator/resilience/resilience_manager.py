"""
Resilience Manager for Self-Healing Photonic Systems (Phase 3.3).
Implements failure tolerance, alternative topologies, and adaptive reconfiguration.
"""

import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import copy

logger = logging.getLogger(__name__)

class FailureType(Enum):
    """Types of failures that can occur in photonic systems."""
    WAVEGUIDE_DEFECT = "waveguide_defect"
    RESONATOR_DRIFT = "resonator_drift"
    PHASE_ERROR = "phase_error"
    AMPLITUDE_LOSS = "amplitude_loss"
    COUPLING_VARIATION = "coupling_variation"
    THERMAL_DRIFT = "thermal_drift"
    MANUFACTURING_VARIATION = "manufacturing_variation"

class ResilienceStrategy(Enum):
    """Strategies for achieving resilience."""
    REDUNDANCY = "redundancy"  # Extra components
    RECONFIGURATION = "reconfiguration"  # Alternative paths
    ADAPTIVE_TUNING = "adaptive_tuning"  parameter tuning
    TOPOLOGICAL_PROTECTION = "topological_protection"  # Topologically robust designs
    FRACTAL_RECOVERY = "fractal_recovery"  # Use fractal patterns for recovery

@dataclass
class FailureScenario:
    """Scenario describing a potential failure."""
    failure_type: FailureType
    severity: float  # 0.0 to 1.0
    location: Optional[Tuple[float, float]] = None
    affected_components: List[str] = field(default_factory=list)
    description: str = ""

@dataclass
class AlternativeTopology:
    """Alternative implementation of the same function."""
    topology_id: str
    description: str
    implementation: Dict[str, Any]  # Problem description for this topology
    estimated_cost: Dict[str, float]
    resilience_score: float = 0.0  # 0.0 to 1.0
    performance_score: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResilienceReport:
    """Report on system resilience."""
    original_topology_id: str
    best_alternative_id: str
    resilience_improvement: float  # How much better the alternative is
    failure_scenarios_tested: int
    recommendations: List[str]
    topology_comparison: Dict[str, Dict[str, float]]  # Scores for each topology
    recovery_paths: Dict[str, List[str]]  # How to recover from each failure

class ResilienceManager:
    """
    Manages system resilience: generates alternatives, tests failures, recommends recovery.
    
    This is Phase 3.3: Enabling self-healing capabilities in SpectraVortex.
    """
    
    def __init__(self, solver_manager=None):
        """
        Initialize the resilience manager.
        
        Args:
            solver_manager: Optional solver manager for evaluating topologies
        """
        self.solver_manager = solver_manager
        self.failure_models: Dict[FailureType, Callable] = {}
        self.topology_generators: Dict[str, Callable] = {}
        self.resilience_cache: Dict[str, ResilienceReport] = {}
        
        # Initialize default failure models
        self._init_failure_models()
        self._init_topology_generators()
        
        logger.info("ResilienceManager initialized (Phase 3.3: Self-Healing)")
    
    def _init_failure_models(self):
        """Initialize default failure models."""
        self.failure_models[FailureType.WAVEGUIDE_DEFECT] = self._simulate_waveguide_defect
        self.failure_models[FailureType.RESONATOR_DRIFT] = self._simulate_resonator_drift
        self.failure_models[FailureType.PHASE_ERROR] = self._simulate_phase_error
        self.failure_models[FailureType.MANUFACTURING_VARIATION] = self._simulate_manufacturing_variation
        
        logger.debug(f"Initialized {len(self.failure_models)} failure models")
    
    def _init_topology_generators(self):
        """Initialize topology generators for common functions."""
        self.topology_generators["oam_multiplexer"] = self._generate_oam_multiplexer_topologies
        self.topology_generators["star_coupler"] = self._generate_star_coupler_topologies
        self.topology_generators["ring_resonator"] = self._generate_ring_resonator_topologies
        
        logger.debug(f"Initialized {len(self.topology_generators)} topology generators")
    
    def analyze_resilience(self, problem: Dict[str, Any]) -> ResilienceReport:
        """
        Analyze resilience of a solution and generate alternatives.
        
        Args:
            problem: Original problem description
        
        Returns:
            ResilienceReport with analysis and recommendations
        """
        start_time = time.time()
        logger.info(f"Resilience analysis for: {problem.get('name', 'unnamed')}")
        
        # Generate alternative topologies
        alternatives = self.generate_alternative_topologies(problem)
        
        if not alternatives:
            logger.warning("No alternative topologies generated")
            return self._create_empty_report(problem)
        
        # Test each topology against failure scenarios
        tested_alternatives = []
        for alt in alternatives:
            resilience_score = self.evaluate_topology_resilience(alt, problem)
            alt.resilience_score = resilience_score
            tested_alternatives.append(alt)
        
        # Find the best alternative
        best_alt = max(tested_alternatives, key=lambda x: x.resilience_score * 0.7 + x.performance_score * 0.3)
        
        # Compare with original (assuming original is first alternative)
        original_score = tested_alternatives[0].resilience_score if tested_alternatives else 0.0
        improvement = best_alt.resilience_score - original_score
        
        # Generate recovery paths
        recovery_paths = self.generate_recovery_paths(problem, tested_alternatives)
        
        # Create report
        report = ResilienceReport(
            original_topology_id=alternatives[0].topology_id,
            best_alternative_id=best_alt.topology_id,
            resilience_improvement=improvement,
            failure_scenarios_tested=len(self._generate_failure_scenarios(problem)),
            recommendations=self._generate_recommendations(best_alt, improvement),
            topology_comparison={
                alt.topology_id: {
                    "resilience": alt.resilience_score,
                    "performance": alt.performance_score,
                    "cost": alt.estimated_cost.get("complexity", 1.0),
                }
                for alt in tested_alternatives
            },
            recovery_paths=recovery_paths,
        )
        
        # Cache the report
        cache_key = f"{problem.get('name', 'unknown')}_{int(time.time())}"
        self.resilience_cache[cache_key] = report
        
        elapsed = time.time() - start_time
        logger.info(f"Resilience analysis completed in {elapsed:.2f}s")
        logger.info(f"Best topology: {best_alt.topology_id} (improvement: {improvement:.2%})")
        
        return report
    
    def generate_alternative_topologies(self, problem: Dict[str, Any]) -> List[AlternativeTopology]:
        """
        Generate alternative implementations for the same function.
        
        Args:
            problem: Original problem description
        
        Returns:
            List of alternative topologies
        """
        alternatives = []
        
        # Add original as first alternative
        original_alt = AlternativeTopology(
            topology_id="original",
            description="Original implementation",
            implementation=problem.copy(),
            estimated_cost=self._estimate_topology_cost(problem),
            resilience_score=0.5,  # Baseline
            performance_score=1.0,  # Original is optimal by design
        )
        alternatives.append(original_alt)
        
        # Check if we have a generator for this problem type
        problem_type = self._identify_problem_type(problem)
        
        if problem_type in self.topology_generators:
            generated = self.topology_generators[problem_type](problem)
            alternatives.extend(generated)
        else:
            # Generic topology variations
            alternatives.extend(self._generate_generic_alternatives(problem))
        
        logger.info(f"Generated {len(alternatives)} alternative topologies for {problem_type}")
        return alternatives
    
    def evaluate_topology_resilience(self, topology: AlternativeTopology, 
                                    original_problem: Dict[str, Any]) -> float:
        """
        Evaluate how resilient a topology is to failures.
        
        Args:
            topology: Alternative topology to test
            original_problem: Original problem for context
        
        Returns:
            Resilience score from 0.0 to 1.0
        """
        failure_scenarios = self._generate_failure_scenarios(original_problem)
        
        if not failure_scenarios:
            return 0.5  # Default score if no failures to test
        
        scores = []
        
        for scenario in failure_scenarios[:5]:  # Test up to 5 scenarios for speed
            try:
                # Apply failure to the topology
                failed_topology = self.apply_failure(topology.implementation, scenario)
                
                # Estimate performance degradation
                original_perf = self._estimate_topology_performance(topology.implementation)
                failed_perf = self._estimate_topology_performance(failed_topology)
                
                if original_perf > 0:
                    degradation = 1.0 - (failed_perf / original_perf)
                    # Score is inverse of degradation (less degradation = more resilient)
                    scenario_score = 1.0 - degradation
                    scores.append(max(0.0, min(1.0, scenario_score)))
                
            except Exception as e:
                logger.debug(f"Error testing failure scenario {scenario.failure_type}: {e}")
                scores.append(0.3)  # Penalty for failure during testing
        
        if not scores:
            return 0.5
        
        # Weight scores by failure severity
        weighted_scores = []
        for i, score in enumerate(scores):
            if i < len(failure_scenarios):
                severity = failure_scenarios[i].severity
                # Severe failures matter more for resilience score
                weighted_scores.append(score * (0.3 + 0.7 * severity))
        
        return float(np.mean(weighted_scores)) if weighted_scores else 0.5
    
    def apply_failure(self, topology: Dict[str, Any], 
                     scenario: FailureScenario) -> Dict[str, Any]:
        """
        Apply a failure scenario to a topology.
        
        Args:
            topology: Topology implementation
            scenario: Failure scenario to apply
        
        Returns:
            Modified topology with failure applied
        """
        if scenario.failure_type in self.failure_models:
            return self.failure_models[scenario.failure_type](topology, scenario)
        
        # Default: add failure metadata
        failed_topology = copy.deepcopy(topology)
        if 'metadata' not in failed_topology:
            failed_topology['metadata'] = {}
        
        failed_topology['metadata']['applied_failure'] = {
            'type': scenario.failure_type.value,
            'severity': scenario.severity,
            'description': scenario.description,
        }
        
        return failed_topology
    
    def generate_recovery_paths(self, original_problem: Dict[str, Any],
                               alternatives: List[AlternativeTopology]) -> Dict[str, List[str]]:
        """
        Generate recovery paths from failures to alternative topologies.
        
        Args:
            original_problem: Original problem
            alternatives: Available alternative topologies
        
        Returns:
            Dictionary mapping failure types to recovery topology IDs
        """
        recovery_paths = {}
        failure_scenarios = self._generate_failure_scenarios(original_problem)
        
        for scenario in failure_scenarios:
            # Find best alternative for this specific failure
            best_alt = self._find_best_recovery(scenario, alternatives)
            if best_alt:
                recovery_paths[scenario.failure_type.value] = [best_alt.topology_id]
                
                # Also suggest reconfiguration strategy
                strategy = self._suggest_recovery_strategy(scenario, best_alt)
                if strategy:
                    recovery_paths[scenario.failure_type.value].append(f"strategy:{strategy.value}")
        
        return recovery_paths
    
    def _generate_oam_multiplexer_topologies(self, problem: Dict[str, Any]) -> List[AlternativeTopology]:
        """Generate alternative topologies for OAM multiplexing."""
        alternatives = []
        
        # Alternative 1: Star coupler based (original)
        star_coupler_alt = AlternativeTopology(
            topology_id="oam_star_coupler",
            description="Star coupler with phased array outputs",
            implementation=self._create_star_coupler_oam(problem),
            estimated_cost={"time_seconds": 1.5, "memory_mb": 200, "complexity": 2.0},
            performance_score=0.9,
            metadata={"type": "star_coupler", "ports": 26},
        )
        alternatives.append(star_coupler_alt)
        
        # Alternative 2: Cascaded ring resonators
        ring_cascade_alt = AlternativeTopology(
            topology_id="oam_ring_cascade",
            description="Cascaded ring resonators with mode selectivity",
            implementation=self._create_ring_cascade_oam(problem),
            estimated_cost={"time_seconds": 2.0, "memory_mb": 250, "complexity": 2.5},
            performance_score=0.85,
            metadata={"type": "ring_cascade", "rings": 8},
        )
        alternatives.append(ring_cascade_alt)
        
        # Alternative 3: Fractal OAM generator
        fractal_alt = AlternativeTopology(
            topology_id="oam_fractal",
            description="Fractal waveguide pattern for OAM generation",
            implementation=self._create_fractal_oam(problem),
            estimated_cost={"time_seconds": 2.5, "memory_mb": 300, "complexity": 3.0},
            performance_score=0.8,
            metadata={"type": "fractal", "levels": 3},
        )
        alternatives.append(fractal_alt)
        
        # Alternative 4: Reconfigurable MZI network
        mzi_alt = AlternativeTopology(
            topology_id="oam_mzi_network",
            description="Reconfigurable Mach-Zehnder interferometer network",
            implementation=self._create_mzi_oam(problem),
            estimated_cost={"time_seconds": 3.0, "memory_mb": 350, "complexity": 3.5},
            performance_score=0.75,
            metadata={"type": "mzi_network", "reconfigurable": True},
        )
        alternatives.append(mzi_alt)
        
        return alternatives
    
    def _generate_star_coupler_topologies(self, problem: Dict[str, Any]) -> List[AlternativeTopology]:
        """Generate alternative topologies for star couplers."""
        alternatives = []
        
        # Different port counts and geometries
        for ports in [16, 24, 32]:
            alt = AlternativeTopology(
                topology_id=f"star_coupler_{ports}p",
                description=f"Star coupler with {ports} output ports",
                implementation=self._modify_star_coupler(problem, ports=ports),
                estimated_cost={"time_seconds": 1.0 + ports/50, "memory_mb": 100 + ports*2, "complexity": 1.0 + ports/30},
                performance_score=0.9 - (ports-16)*0.01,  # Slightly worse with more ports
                metadata={"ports": ports, "redundancy": "high" if ports > 24 else "medium"},
            )
            alternatives.append(alt)
        
        return alternatives
    
    def _generate_ring_resonator_topologies(self, problem: Dict[str, Any]) -> List[AlternativeTopology]:
        """Generate alternative topologies for ring resonators."""
        alternatives = []
        
        # Single ring vs coupled rings
        alt_single = AlternativeTopology(
            topology_id="ring_single",
            description="Single ring resonator",
            implementation=self._modify_ring_resonator(problem, coupled=False),
            estimated_cost={"time_seconds": 0.8, "memory_mb": 80, "complexity": 1.0},
            performance_score=0.7,
            metadata={"type": "single", "q_factor": "high"},
        )
        alternatives.append(alt_single)
        
        alt_coupled = AlternativeTopology(
            topology_id="ring_coupled",
            description="Coupled ring resonator (photonic molecule)",
            implementation=self._modify_ring_resonator(problem, coupled=True),
            estimated_cost={"time_seconds": 1.5, "memory_mb": 150, "complexity": 2.0},
            performance_score=0.85,
            metadata={"type": "coupled", "rings": 2, "robustness": "higher"},
        )
        alternatives.append(alt_coupled)
        
        alt_array = AlternativeTopology(
            topology_id="ring_array",
            description="Array of ring resonators with redundancy",
            implementation=self._modify_ring_resonator(problem, array=True),
            estimated_cost={"time_seconds": 2.5, "memory_mb": 250, "complexity": 3.0},
            performance_score=0.9,
            metadata={"type": "array", "rings": 4, "redundancy": "high"},
        )
        alternatives.append(alt_array)
        
        return alternatives
    
    def _generate_generic_alternatives(self, problem: Dict[str, Any]) -> List[AlternativeTopology]:
        """Generate generic alternative topologies."""
        alternatives = []
        
        # Alternative with redundancy
        redundant_alt = AlternativeTopology(
            topology_id="redundant",
            description="Implementation with redundant components",
            implementation=self._add_redundancy(problem),
            estimated_cost=self._estimate_topology_cost(problem, redundancy_factor=1.5),
            performance_score=0.8,
            metadata={"strategy": "redundancy", "redundancy_factor": 1.5},
        )
        alternatives.append(redundant_alt)
        
        # Alternative with wider tolerances
        tolerant_alt = AlternativeTopology(
            topology_id="tolerant",
            description="Implementation tolerant to manufacturing variations",
            implementation=self._increase_tolerances(problem),
            estimated_cost=self._estimate_topology_cost(problem, tolerance_factor=2.0),
            performance_score=0.75,
            metadata={"strategy": "tolerance", "tolerance_factor": 2.0},
        )
        alternatives.append(tolerant_alt)
        
        return alternatives
    
    def _simulate_waveguide_defect(self, topology: Dict[str, Any], 
                                  scenario: FailureScenario) -> Dict[str, Any]:
        """Simulate a waveguide defect (e.g., width variation, surface roughness)."""
        failed = copy.deepcopy(topology)
        
        # Modify waveguide parameters
        if 'components' in failed:
            for comp in failed['components']:
                if 'waveguide' in comp.get('type', ''):
                    # Add width variation
                    original_width = comp.get('width', 0.5e-6)
                    variation = scenario.severity * 0.2e-6  # Up to 200nm variation
                    comp['width'] = original_width + variation * np.random.randn()
                    
                    # Add propagation loss
                    if 'loss' not in comp:
                        comp['loss'] = 0.0
                    comp['loss'] += scenario.severity * 10.0  # dB/cm
        
        return failed
    
    def _simulate_resonator_drift(self, topology: Dict[str, Any],
                                 scenario: FailureScenario) -> Dict[str, Any]:
        """Simulate resonator frequency drift (e.g., thermal, aging)."""
        failed = copy.deepcopy(topology)
        
        if 'components' in failed:
            for comp in failed['components']:
                if any(term in comp.get('type', '') for term in ['resonator', 'ring']):
                    # Shift resonance frequency
                    if 'resonance_frequency' in comp:
                        drift = scenario.severity * 0.01  # Up to 1% drift
                        comp['resonance_frequency'] *= (1 + drift * np.random.randn())
                    
                    # Degrade Q factor
                    if 'q_factor' in comp:
                        degradation = 1.0 - scenario.severity * 0.5  # Up to 50% degradation
                        comp['q_factor'] *= degradation
        
        return failed
    
    def _simulate_phase_error(self, topology: Dict[str, Any],
                             scenario: FailureScenario) -> Dict[str, Any]:
        """Simulate phase errors in interferometric components."""
        failed = copy.deepcopy(topology)
        
        if 'parameters' not in failed:
            failed['parameters'] = {}
        
        # Add random phase errors
        phase_error = scenario.severity * np.pi / 4  # Up to 45 degree error
        failed['parameters']['phase_error'] = phase_error * np.random.randn()
        
        # Add to metadata
        if 'metadata' not in failed:
            failed['metadata'] = {}
        failed['metadata']['phase_errors_applied'] = True
        
        return failed
    
    def _simulate_manufacturing_variation(self, topology: Dict[str, Any],
                                        scenario: FailureScenario) -> Dict[str, Any]:
        """Simulate manufacturing process variations."""
        failed = copy.deepcopy(topology)
        
        # Apply global manufacturing variations
        variation = scenario.severity * 0.1  # Up to 10% variation
        
        if 'components' in failed:
            for comp in failed['components']:
                # Vary all dimensional parameters
                for key in ['width', 'height', 'length', 'radius', 'thickness']:
                    if key in comp:
                        comp[key] *= (1 + variation * np.random.randn())
                
                # Vary material properties
                if 'material' in comp and comp['material'] == 'silicon':
                    # Silicon refractive index variation
                    if 'refractive_index' not in comp:
                        comp['refractive_index'] = 3.47
                    comp['refractive_index'] += variation * 0.01 * np.random.randn()
        
        return failed
    
    def _create_star_coupler_oam(self, original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Create star coupler based OAM multiplexer."""
        problem = copy.deepcopy(original_problem)
        problem['name'] = f"{problem.get('name', '')}_star_coupler"
        
        # Star coupler specific parameters
        problem['components'] = [
            {"type": "star_coupler", "ports": 26, "radius": 15e-6},
            {"type": "waveguide_array", "count": 26, "spacing": 1.0e-6},
        ]
        
        problem['parameters']['oam_generation_method'] = "star_coupler_phased_array"
        problem['metadata']['resilience_features'] = ["redundant_ports", "phase_tunable"]
        
        return problem
    
    def _create_ring_cascade_oam(self, original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Create ring resonator cascade OAM multiplexer."""
        problem = copy.deepcopy(original_problem)
        problem['name'] = f"{problem.get('name', '')}_ring_cascade"
        
        # Ring cascade specific parameters
        problem['components'] = [
            {"type": "ring_resonator", "radius": 5e-6, "q_factor": 10000},
            {"type": "ring_resonator", "radius": 5.2e-6, "q_factor": 10000},
            {"type": "ring_resonator", "radius": 5.4e-6, "q_factor": 10000},
            {"type": "ring_resonator", "radius": 5.6e-6, "q_factor": 10000},
        ]
        
        problem['parameters']['oam_generation_method'] = "ring_cascade_mode_selective"
        problem['metadata']['resilience_features'] = ["coupled_rings", "frequency_diversity"]
        
        return problem
    
    def _create_fractal_oam(self, original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Create fractal pattern OAM generator."""
        problem = copy.deepcopy(original_problem)
        problem['name'] = f"{problem.get('name', '')}_fractal"
        
        # Fractal specific parameters
        problem['components'] = [
            {"type": "fractal_waveguide", "levels": 3, "branching_factor": 2},
            {"type": "phase_control_array", "elements": 8},
        ]
        
        problem['parameters']['oam_generation_method'] = "fractal_interference"
        problem['metadata']['resilience_features'] = ["fractal_redundancy", "self_similar", "multiple_paths"]
        
        return problem
    
    def _create_mzi_oam(self, original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Create MZI network OAM generator."""
        problem = copy.deepcopy(original_problem)
        problem['name'] = f"{problem.get('name', '')}_mzi_network"
        
        # MZI network specific parameters
        problem['components'] = [
            {"type": "mzi", "count": 4, "reconfigurable": True},
            {"type": "phase_shifter", "count": 8},
        ]
        
        problem['parameters']['oam_generation_method'] = "reconfigurable_interferometer"
        problem['metadata']['resilience_features'] = ["fully_reconfigurable", "adaptive", "software_defined"]
        
        return problem
    
    def _modify_star_coupler(self, original_problem: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Modify star coupler parameters."""
        problem = copy.deepcopy(original_problem)
        # Implementation would modify component parameters
        return problem
    
    def _modify_ring_resonator(self, original_problem: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Modify ring resonator parameters."""
        problem = copy.deepcopy(original_problem)
        # Implementation would modify component parameters
        return problem
    
    def _add_redundancy(self, original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Add redundant components to a topology."""
        problem = copy.deepcopy(original_problem)
        
        if 'components' in problem:
            # Duplicate critical components
            critical_components = []
            for comp in problem['components']:
                if any(term in comp.get('type', '') for term in ['resonator', 'coupler', 'splitter']):
                    critical_components.append(copy.deepcopy(comp))
            
            # Add redundant copies
            problem['components'].extend(critical_components)
            
            # Add metadata
            if 'metadata' not in problem:
                problem['metadata'] = {}
            problem['metadata']['redundant_components'] = len(critical_components)
            problem['metadata']['resilience_strategy'] = "redundancy"
        
        return problem
    
    def _increase_tolerances(self, original_problem: Dict[str, Any]) -> Dict[str, Any]:
        """Increase manufacturing tolerances."""
        problem = copy.deepcopy(original_problem)
        
        # Add tolerance specifications
        if 'manufacturing' not in problem:
            problem['manufacturing'] = {}
        
        problem['manufacturing']['tolerances'] = {
            'width': '±100nm',  # Increased from typical ±50nm
            'thickness': '±20nm',
            'etch_depth': '±30nm',
            'alignment': '±150nm',
        }
        
        if 'metadata' not in problem:
            problem['metadata'] = {}
        problem['metadata']['tolerance_level'] = "high"
        problem['metadata']['resilience_strategy'] = "tolerance"
        
        return problem
    
    def _identify_problem_type(self, problem: Dict[str, Any]) -> str:
        """Identify the type of problem for topology generation."""
        name = problem.get('name', '').lower()
        components = problem.get('components', [])
        
        if any('oam' in str(c).lower() for c in components) or 'oam' in name:
            return "oam_multiplexer"
        elif any('star' in str(c).lower() for c in components) or 'star' in name:
            return "star_coupler"
        elif any('ring' in str(c).lower() for c in components) or 'ring' in name:
            return "ring_resonator"
        else:
            return "generic"
    
    def _generate_failure_scenarios(self, problem: Dict[str, Any]) -> List[FailureScenario]:
        """Generate relevant failure scenarios for a problem."""
        scenarios = []
        
        # Common failures for photonic systems
        scenarios.append(FailureScenario(
            failure_type=FailureType.MANUFACTURING_VARIATION,
            severity=0.3,
            description="Typical process variations (±10nm waveguide width)"
        ))
        
        scenarios.append(FailureScenario(
            failure_type=FailureType.THERMAL_DRIFT,
            severity=0.4,
            description="Temperature variation causing resonance drift"
        ))
        
        scenarios.append(FailureScenario(
            failure_type=FailureType.WAVEGUIDE_DEFECT,
            severity=0.2,
            description="Localized waveguide defects or surface roughness"
        ))
        
        # Problem-specific failures
        problem_type = self._identify_problem_type(problem)
        
        if problem_type == "oam_multiplexer":
            scenarios.append(FailureScenario(
                failure_type=FailureType.PHASE_ERROR,
                severity=0.5,
                description="Phase errors in OAM interference patterns",
                affected_components=["phase_shifters", "interferometers"]
            ))
        
        if problem_type == "ring_resonator":
            scenarios.append(FailureScenario(
                failure_type=FailureType.RESONATOR_DRIFT,
                severity=0.6,
                description="Resonator frequency drift due to aging or temperature",
                affected_components=["ring_resonators", "racetrack_resonators"]
            ))
        
        return scenarios
    
    def _estimate_topology_cost(self, topology: Dict[str, Any], **kwargs) -> Dict[str, float]:
        """Estimate computational cost of a topology."""
        # Simple heuristic based on problem complexity
        complexity = 1.0
        
        if 'components' in topology:
            complexity += len(topology['components']) * 0.2
        
        # Apply modifiers
        redundancy_factor = kwargs.get('redundancy_factor', 1.0)
        tolerance_factor = kwargs.get('tolerance_factor', 1.0)
        
        complexity *= redundancy_factor * tolerance_factor
        
        return {
            "time_seconds": complexity * 1.0,
            "memory_mb": complexity * 100,
            "complexity": complexity,
        }
    
    def _estimate_topology_performance(self, topology: Dict[str, Any]) -> float:
        """Estimate performance of a topology (0.0 to 1.0)."""
        # Base performance
        performance = 0.8
        
        # Adjust based on complexity (simpler often performs better)
        if 'components' in topology:
            component_count = len(topology['components'])
            if component_count < 5:
                performance += 0.1
            elif component_count > 10:
                performance -= 0.1
        
        # Adjust based on resilience features
        if 'metadata' in topology:
            metadata = topology['metadata']
            if metadata.get('redundancy_factor', 1.0) > 1.2:
                performance -= 0.05  # Redundancy has small performance cost
            if metadata.get('tolerance_level') == "high":
                performance += 0.05  # High tolerance can improve yield
        
        return max(0.0, min(1.0, performance))
    
    def _find_best_recovery(self, scenario: FailureScenario, 
                           alternatives: List[AlternativeTopology]) -> Optional[AlternativeTopology]:
        """Find best alternative topology for recovering from a failure."""
        if not alternatives:
            return None
        
        # Simple heuristic: choose topology with highest resilience score
        return max(alternatives, key=lambda x: x.resilience_score)
    
    def _suggest_recovery_strategy(self, scenario: FailureScenario,
                                 best_alt: AlternativeTopology) -> Optional[ResilienceStrategy]:
        """Suggest recovery strategy for a failure."""
        if scenario.failure_type == FailureType.WAVEGUIDE_DEFECT:
            return ResilienceStrategy.RECONFIGURATION
        elif scenario.failure_type == FailureType.RESONATOR_DRIFT:
            return ResilienceStrategy.ADAPTIVE_TUNING
        elif scenario.failure_type == FailureType.MANUFACTURING_VARIATION:
            return ResilienceStrategy.TOPOLOGICAL_PROTECTION
        elif 'fractal' in best_alt.topology_id:
            return ResilienceStrategy.FRACTAL_RECOVERY
        else:
            return ResilienceStrategy.REDUNDANCY
    
    def _generate_recommendations(self, best_alt: AlternativeTopology, 
                                improvement: float) -> List[str]:
        """Generate recommendations based on resilience analysis."""
        recommendations = []
        
        if improvement > 0.2:
            recommendations.append(f"Consider switching to {best_alt.topology_id} "
                                  f"(resilience improvement: {improvement:.1%})")
        
        if best_alt.estimated_cost.get('complexity', 1.0) > 2.0:
            recommendations.append("Note: Higher complexity may increase fabrication cost")
        
        metadata = best_alt.metadata
        if metadata.get('redundant_components', 0) > 0:
            recommendations.append(f"Design includes {metadata['redundant_components']} "
                                  "redundant components for fault tolerance")
        
        if 'resilience_features' in metadata:
            features = metadata['resilience_features']
            if features:
                recommendations.append(f"Resilience features: {', '.join(features)}")
        
        if improvement < 0.05:
            recommendations.append("Original design is already reasonably resilient. "
                                  "Consider if improvement justifies complexity increase.")
        
        return recommendations
    
    def _create_empty_report(self, problem: Dict[str, Any]) -> ResilienceReport:
        """Create empty report when analysis fails."""
        return ResilienceReport(
            original_topology_id="original",
            best_alternative_id="original",
            resilience_improvement=0.0,
            failure_scenarios_tested=0,
            recommendations=["Resilience analysis unavailable"],
            topology_comparison={},
            recovery_paths={},
        )

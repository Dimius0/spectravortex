"""
Topological Analysis for Photonic Circuits.
"""

import numpy as np
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TopologicalFeature:
    """
    Represents a topological feature in a photonic field.
    Used for analyzing circuit robustness and identifying critical regions.
    """
    feature_type: str  # 'singularity', 'vortex', 'wavefront_discontinuity', etc.
    location: Tuple[float, float]  # (x, y) coordinates
    magnitude: float = 1.0  # Strength of the feature
    complexity: float = 0.0  # Computed complexity score
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize computed fields."""
        if self.complexity == 0.0:
            self.complexity = self._calculate_complexity()
    
    def _calculate_complexity(self) -> float:
        """Calculate complexity based on feature type and magnitude."""
        base_complexity = {
            'singularity': 2.0,
            'vortex': 1.5,
            'wavefront_discontinuity': 1.0,
            'phase_singularity': 2.5,
            'amplitude_null': 0.8,
            'interference_maxima': 0.5,
            'interference_minima': 0.5,
            'boundary_discontinuity': 1.2,
            'waveguide_defect': 1.8,
            'resonator_drift': 1.3,
            'material_imperfection': 0.9,
            'coupling_variation': 1.1
        }.get(self.feature_type, 1.0)
        
        return base_complexity * self.magnitude
    
    def analyze_complexity(self) -> float:
        """Public method to analyze feature complexity."""
        return self.complexity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'feature_type': self.feature_type,
            'location': self.location,
            'magnitude': self.magnitude,
            'complexity': self.complexity,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopologicalFeature':
        """Create from dictionary."""
        # Handle different input formats
        location = data.get('location', (0.0, 0.0))
        if isinstance(location, list):
            location = tuple(location)
        
        return cls(
            feature_type=data.get('feature_type', 'unknown'),
            location=location,
            magnitude=data.get('magnitude', 1.0),
            complexity=data.get('complexity', 0.0),
            metadata=data.get('metadata', {})
        )


def analyze_topological_features(field_amplitude: np.ndarray, 
                                field_phase: np.ndarray,
                                threshold: float = 0.1) -> List[TopologicalFeature]:
    """
    Analyze topological features in a photonic field.
    
    Args:
        field_amplitude: Amplitude field
        field_phase: Phase field
        threshold: Detection threshold
        
    Returns:
        List of detected topological features
    """
    features = []
    
    # Basic topological feature detection (simplified)
    if field_amplitude is not None and field_phase is not None:
        # Detect amplitude nulls (zeros in amplitude)
        null_indices = np.where(field_amplitude < threshold)
        for i, j in zip(null_indices[0], null_indices[1]):
            if i < len(field_amplitude) and j < len(field_amplitude[0]):
                features.append(TopologicalFeature(
                    feature_type='amplitude_null',
                    location=(float(i), float(j)),
                    magnitude=float(field_amplitude[i, j]),
                    metadata={'field_type': 'amplitude'}
                ))
        
        # Detect phase singularities (rapid phase changes)
        if len(field_phase.shape) == 2:
            # Simple gradient-based detection
            grad_x = np.gradient(field_phase, axis=0)
            grad_y = np.gradient(field_phase, axis=1)
            
            # Find regions with high phase gradient
            grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            singularity_indices = np.where(grad_magnitude > np.pi)
            
            for i, j in zip(singularity_indices[0], singularity_indices[1]):
                if i < len(field_phase) and j < len(field_phase[0]):
                    features.append(TopologicalFeature(
                        feature_type='phase_singularity',
                        location=(float(i), float(j)),
                        magnitude=float(grad_magnitude[i, j]),
                        metadata={'field_type': 'phase'}
                    ))
    
    return features


def detect_boundary_features(boundary_amplitude: np.ndarray,
                           boundary_phase: np.ndarray) -> List[TopologicalFeature]:
    """
    Detect topological features specifically at boundaries.
    
    Args:
        boundary_amplitude: Amplitude at boundary
        boundary_phase: Phase at boundary
        
    Returns:
        List of boundary topological features
    """
    features = []
    
    if boundary_amplitude is not None and len(boundary_amplitude) > 1:
        # Detect discontinuities in amplitude
        amp_diff = np.diff(boundary_amplitude)
        large_diffs = np.where(np.abs(amp_diff) > 0.5)[0]
        
        for idx in large_diffs:
            features.append(TopologicalFeature(
                feature_type='boundary_discontinuity',
                location=(float(idx), 0.0),
                magnitude=float(np.abs(amp_diff[idx])),
                metadata={'boundary_type': 'amplitude_discontinuity'}
            ))
    
    if boundary_phase is not None and len(boundary_phase) > 1:
        # Detect phase jumps (wrapped phase differences)
        phase_diff = np.diff(boundary_phase)
        phase_jumps = np.where(np.abs(phase_diff) > np.pi/2)[0]
        
        for idx in phase_jumps:
            features.append(TopologicalFeature(
                feature_type='phase_discontinuity',
                location=(float(idx), 0.0),
                magnitude=float(np.abs(phase_diff[idx])),
                metadata={'boundary_type': 'phase_jump'}
            ))
    
    return features


def calculate_topological_complexity(features: List[TopologicalFeature]) -> float:
    """
    Calculate overall topological complexity from features.
    
    Args:
        features: List of topological features
        
    Returns:
        Overall complexity score
    """
    if not features:
        return 0.0
    
    total_complexity = sum(feat.complexity for feat in features)
    return total_complexity / len(features)


def features_to_report(features: List[TopologicalFeature]) -> Dict[str, Any]:
    """
    Convert topological features to a report dictionary.
    
    Args:
        features: List of topological features
        
    Returns:
        Report dictionary
    """
    if not features:
        return {
            'feature_count': 0,
            'total_complexity': 0.0,
            'feature_types': [],
            'summary': 'No topological features detected'
        }
    
    # Count by type
    type_counts = {}
    for feat in features:
        type_counts[feat.feature_type] = type_counts.get(feat.feature_type, 0) + 1
    
    # Calculate statistics
    max_complexity = max(feat.complexity for feat in features)
    avg_complexity = sum(feat.complexity for feat in features) / len(features)
    
    return {
        'feature_count': len(features),
        'total_complexity': sum(feat.complexity for feat in features),
        'average_complexity': avg_complexity,
        'max_complexity': max_complexity,
        'feature_types': type_counts,
        'critical_features': [
            feat.to_dict() for feat in features 
            if feat.complexity > 1.5
        ],
        'summary': f'Detected {len(features)} topological features '
                   f'({len([f for f in features if f.complexity > 1.5])} critical)'
    }
#!/usr/bin/env python3
"""
Auto Router for SpectraVortex
Automatically route waveguides between photonic components.
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import heapq

class RoutingPort:
    """Port for component connection."""
    def __init__(self, component_id: str, port_name: str, x: float, y: float, direction: float):
        self.component_id = component_id
        self.port_name = port_name
        self.x = x
        self.y = y
        self.direction = direction  # radians (0 = right, π/2 = up, etc.)
        self.port_type = "optical"
    
    def get_endpoint(self, offset: float = 5.0) -> Tuple[float, float]:
        """Get point offset from port in direction."""
        return (
            self.x + offset * math.cos(self.direction),
            self.y + offset * math.sin(self.direction)
        )

class AutoRouter:
    """Automatic waveguide router for photonic chips."""
    
    def __init__(self, technology: str = "silicon_photonic_220nm"):
        """
        Initialize auto router.
        
        Args:
            technology: Technology process name
        """
        self.technology = technology
        self.grid_size = 2.0  # μm grid for routing
        self.min_bend_radius = 5.0
        self.waveguide_width = 0.5
        
        # Routing grid for obstacle avoidance
        self.obstacle_grid: Dict[Tuple[int, int], bool] = {}
        self.components: List[Any] = []
        self.ports: List[RoutingPort] = []
        self.component_positions: Dict[str, Tuple[float, float]] = {}
        
    def add_component(self, component: Any, x: float, y: float) -> str:
        """
        Add component to routing space.
        
        Args:
            component: Photonic component
            x, y: Position
            
        Returns:
            Component ID
        """
        comp_id = f"comp_{len(self.components)}"
        
        # Store component with position
        self.components.append(component)
        self.component_positions[comp_id] = (x, y)
        
        # Mark component area as obstacle
        self._mark_component_area(comp_id, x, y)
        
        # Create ports for the component
        self._create_ports_for_component(component, comp_id, x, y)
        
        return comp_id
    
    def _mark_component_area(self, comp_id: str, x: float, y: float):
        """Mark component area as obstacle on grid."""
        # Simple bounding box approximation
        width = 20.0  # Default component width
        height = 20.0  # Default component height
        
        # Mark grid cells occupied by component
        x_min = int((x - width/2) / self.grid_size)
        x_max = int((x + width/2) / self.grid_size)
        y_min = int((y - height/2) / self.grid_size)
        y_max = int((y + height/2) / self.grid_size)
        
        for gx in range(x_min, x_max + 1):
            for gy in range(y_min, y_max + 1):
                self.obstacle_grid[(gx, gy)] = True
    
    def _create_ports_for_component(self, component: Any, comp_id: str, x: float, y: float):
        """Create routing ports for a component."""
        # Get component type name
        comp_type = type(component).__name__
        
        if comp_type == 'MZIInterferometer':
            # MZI has input and output ports
            self.ports.append(RoutingPort(
                component_id=comp_id, port_name="input",
                x=x - 10, y=y, direction=0
            ))
            self.ports.append(RoutingPort(
                component_id=comp_id, port_name="output", 
                x=x + 10, y=y, direction=math.pi
            ))
        elif comp_type == 'OAMModeConverter':
            # OAM converter has single port
            self.ports.append(RoutingPort(
                component_id=comp_id, port_name="io",
                x=x, y=y + 10, direction=-math.pi/2
            ))
        elif comp_type == 'Waveguide':
            # Waveguide has start and end ports
            self.ports.append(RoutingPort(
                component_id=comp_id, port_name="start",
                x=x, y=y, direction=0
            ))
            if hasattr(component, 'length'):
                self.ports.append(RoutingPort(
                    component_id=comp_id, port_name="end",
                    x=x + component.length, y=y, direction=math.pi
                ))
        else:
            # Generic component
            self.ports.append(RoutingPort(
                component_id=comp_id, port_name="port1",
                x=x, y=y, direction=0
            ))
            self.ports.append(RoutingPort(
                component_id=comp_id, port_name="port2",
                x=x, y=y + 10, direction=math.pi/2
            ))
    
    def find_path_a_star(self, start: Tuple[float, float], 
                        end: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """
        Find path using A* algorithm.
        
        Args:
            start: (x, y) start point
            end: (x, y) end point
            
        Returns:
            List of points forming the path, or None if no path found
        """
        # Convert to grid coordinates
        start_grid = (int(start[0] / self.grid_size), int(start[1] / self.grid_size))
        end_grid = (int(end[0] / self.grid_size), int(end[1] / self.grid_size))
        
        # Priority queue for A*
        open_set = []
        heapq.heappush(open_set, (0, start_grid))
        
        # Navigation data
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start_grid: None}
        g_score: Dict[Tuple[int, int], float] = {start_grid: 0}
        f_score: Dict[Tuple[int, int], float] = {start_grid: self._heuristic(start_grid, end_grid)}
        
        # Directions: 4-connected grid
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == end_grid:
                # Reconstruct path
                path = []
                while current is not None:
                    # Convert back to microns
                    path.append((current[0] * self.grid_size, 
                                current[1] * self.grid_size))
                    current = came_from[current]
                return list(reversed(path))
            
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Check if walkable
                if self.obstacle_grid.get(neighbor, False):
                    continue
                
                # Calculate tentative score
                tentative_g = g_score[current] + self.grid_size
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end_grid)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None  # No path found
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Heuristic for A* (Manhattan distance)."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def connect_components(self, comp_id1: str, port1: str, 
                          comp_id2: str, port2: str) -> Optional[Any]:
        """
        Connect two components with a waveguide.
        
        Args:
            comp_id1, comp_id2: Component IDs
            port1, port2: Port names
            
        Returns:
            Created Waveguide object, or None if routing failed
        """
        # Find ports
        port_a = next((p for p in self.ports 
                      if p.component_id == comp_id1 and p.port_name == port1), None)
        port_b = next((p for p in self.ports 
                      if p.component_id == comp_id2 and p.port_name == port2), None)
        
        if not port_a or not port_b:
            print(f"❌ Ports not found: {comp_id1}.{port1} or {comp_id2}.{port2}")
            return None
        
        # Get start and end points (offset from ports)
        start = port_a.get_endpoint(offset=5.0)
        end = port_b.get_endpoint(offset=5.0)
        
        # Find path
        path = self.find_path_a_star(start, end)
        
        if not path:
            print(f"❌ No valid path found between {comp_id1} and {comp_id2}")
            return None
        
        # Add port connections to path
        full_path = [(port_a.x, port_a.y)] + path + [(port_b.x, port_b.y)]
        
        # Calculate total length
        length = self._calculate_path_length(full_path)
        
        # Create waveguide (we'll import Waveguide class only when needed)
        try:
            from .component_library import Waveguide
            waveguide = Waveguide(
                length=length,
                width=self.waveguide_width,
                name=f"route_{comp_id1}_{comp_id2}"
            )
            # Store path points
            waveguide.path_points = full_path
            waveguide.comp_id1 = comp_id1
            waveguide.comp_id2 = comp_id2
            
            print(f"✅ Routed {comp_id1}.{port1} → {comp_id2}.{port2}: {length:.1f}μm")
            return waveguide
            
        except ImportError:
            print(f"⚠️  Cannot create Waveguide: component_library not available")
            return None
    
    def _calculate_path_length(self, path: List[Tuple[float, float]]) -> float:
        """Calculate total length of a path."""
        length = 0.0
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            length += math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return length
    
    def route_all(self, connections: List[Tuple[str, str, str, str]]) -> List[Any]:
        """
        Route multiple connections.
        
        Args:
            connections: List of (comp_id1, port1, comp_id2, port2)
            
        Returns:
            List of created waveguides
        """
        waveguides = []
        
        for comp_id1, port1, comp_id2, port2 in connections:
            waveguide = self.connect_components(comp_id1, port1, comp_id2, port2)
            if waveguide:
                waveguides.append(waveguide)
                # Mark new waveguide as obstacle for subsequent routing
                self._mark_waveguide_area(waveguide)
        
        return waveguides
    
    def _mark_waveguide_area(self, waveguide: Any):
        """Mark waveguide area as obstacle for future routing."""
        if hasattr(waveguide, 'path_points'):
            # Mark points along path
            for x, y in waveguide.path_points:
                gx = int(x / self.grid_size)
                gy = int(y / self.grid_size)
                # Mark cell and neighbors (waveguide has width)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        self.obstacle_grid[(gx + dx, gy + dy)] = True
    
    def generate_simple_demo(self):
        """Generate a simple demo routing."""
        print("🎨 Creating auto-routing demo...")
        
        # Clear any existing data
        self.components = []
        self.ports = []
        self.obstacle_grid = {}
        self.component_positions = {}
        
        try:
            from .component_library import MZIInterferometer, OAMModeConverter
            
            # Add some components
            mzi1_id = self.add_component(
                MZIInterferometer(coupling_ratio=0.5, name="mzi1"),
                x=50, y=50
            )
            
            mzi2_id = self.add_component(
                MZIInterferometer(coupling_ratio=0.5, name="mzi2"),
                x=150, y=100
            )
            
            oam_id = self.add_component(
                OAMModeConverter(target_oam=1, name="oam1"),
                x=100, y=150
            )
            
            # Route connections
            waveguides = self.route_all([
                (mzi1_id, "output", mzi2_id, "input"),
                (mzi2_id, "output", oam_id, "io")
            ])
            
            print(f"✅ Demo created: {len(waveguides)} waveguides routed")
            return waveguides
            
        except ImportError as e:
            print(f"⚠️  Demo requires component_library: {e}")
            return []

def main():
    """Test the auto router."""
    router = AutoRouter()
    
    print("=" * 60)
    print("SpectraVortex Auto Router Test")
    print("=" * 60)
    
    # Generate demo
    waveguides = router.generate_simple_demo()
    
    # Show results
    print(f"\n📊 Routing Results:")
    print(f"   Components placed: {len(router.components)}")
    print(f"   Ports created: {len(router.ports)}")
    print(f"   Waveguides routed: {len(waveguides)}")
    
    for i, wg in enumerate(waveguides, 1):
        if hasattr(wg, 'length'):
            print(f"   {i}. {wg.name}: {wg.length:.1f}μm")
        else:
            print(f"   {i}. {wg.name}: (no length attribute)")
    
    print("\n✅ Auto router test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

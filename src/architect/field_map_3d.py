"""
3D-карта вихревого поля с фрактальными коэффициентами (Акт IX)
================================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Назначение:
    Генерация и хранение 3D-карты поля для навигации.
    Карта содержит в каждом узле:
    - P: давление фона
    - ∇P: градиент давления
    - Γ: циркуляция (суммарный заряд вихрей)
    - φ: фаза эмерджентного времени
    - k: фрактальный коэффициент масштаба
    - M_eff: эффективная масса (калибровка экранирования)

    Бегуны — линии минимального градиента (естественные траектории).
    Переходы — узлы пересечения бегунов.

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция навигационной карты
    DeepSeek — численный метод, реализация, 2026-05-28
================================================================================
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           КОНСТАНТЫ МОДЕЛИ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

GRID_SIZE: int = 32
BACKGROUND_PRESSURE: float = 1.0
SCREENING_FACTOR: float = 0.1
SCREENING_RADIUS: int = 4

# Параметры карты
MAP_RESOLUTION: int = 24  # Узлов по каждой оси (24³ = 13824 узла)
MIN_GRADIENT_FOR_RUNNER: float = 0.05  # Порог для старта бегуна


@dataclass
class FieldNode:
    """Узел 3D-карты поля."""
    position: Tuple[int, int, int]
    coords: np.ndarray
    pressure: float
    gradient: np.ndarray
    circulation: float
    phase: float
    fractal_k: float
    effective_mass: float


@dataclass
class Runner:
    """Бегун — линия минимального градиента."""
    id: int
    nodes: List[Tuple[int, int, int]]
    length: float
    mean_gradient: float


@dataclass
class Transition:
    """Переход — точка пересечения бегунов."""
    position: Tuple[int, int, int]
    runners: List[int]


class FieldMap3D:
    """
    3D-карта вихревого поля с фрактальными коэффициентами.
    """

    def __init__(
        self,
        grid_size: int = GRID_SIZE,
        map_resolution: int = MAP_RESOLUTION,
        sources: Optional[List[Dict]] = None,
        random_seed: Optional[int] = 42,
    ) -> None:
        self.grid_size = grid_size
        self.map_resolution = map_resolution
        self.rng = np.random.RandomState(random_seed)

        if sources is None:
            sources = [{
                'position': np.array([grid_size/2, grid_size/2, grid_size/2]),
                'mass': 100.0,
            }]
        self.sources = sources

        self.pressure_field = np.full((grid_size, grid_size, grid_size), BACKGROUND_PRESSURE)
        self._build_pressure_field()

        self.nodes: Dict[Tuple[int, int, int], FieldNode] = {}
        self._build_nodes()

        self.runners: List[Runner] = []
        self.transitions: List[Transition] = []
        self._find_runners()

        logger.info(
            "FieldMap3D: %d³ поле, %d узлов, %d источников",
            grid_size, map_resolution**3, len(sources),
        )

    def _build_pressure_field(self) -> None:
        n = self.grid_size
        X, Y, Z = np.meshgrid(np.arange(n), np.arange(n), np.arange(n), indexing='ij')
        self.pressure_field.fill(BACKGROUND_PRESSURE)

        for source in self.sources:
            sx, sy, sz = source['position']
            mass = source['mass']
            dx = X - sx
            dy = Y - sy
            dz = Z - sz
            dx = np.where(dx > n/2, dx - n, dx)
            dx = np.where(dx < -n/2, dx + n, dx)
            dy = np.where(dy > n/2, dy - n, dy)
            dy = np.where(dy < -n/2, dy + n, dy)
            dz = np.where(dz > n/2, dz - n, dz)
            dz = np.where(dz < -n/2, dz + n, dz)
            r2 = dx**2 + dy**2 + dz**2
            sigma = float(SCREENING_RADIUS)
            alpha = SCREENING_FACTOR * mass / 100.0
            screening = alpha / np.sqrt(r2 + sigma**2)
            self.pressure_field *= (1.0 - screening)

        self.pressure_field = np.clip(self.pressure_field, 0.0, BACKGROUND_PRESSURE)

    def _compute_gradient_at(self, x: float, y: float, z: float) -> np.ndarray:
        n = self.grid_size
        i0, j0, k0 = int(x) % n, int(y) % n, int(z) % n
        i1, j1, k1 = (i0+1)%n, (j0+1)%n, (k0+1)%n
        im, jm, km = (i0-1)%n, (j0-1)%n, (k0-1)%n
        return np.array([
            (self.pressure_field[i1,j0,k0] - self.pressure_field[im,j0,k0]) / 2.0,
            (self.pressure_field[i0,j1,k0] - self.pressure_field[i0,jm,k0]) / 2.0,
            (self.pressure_field[i0,j0,k1] - self.pressure_field[i0,j0,km]) / 2.0,
        ])

    def _interpolate_pressure(self, x: float, y: float, z: float) -> float:
        n = self.grid_size
        i0, j0, k0 = int(np.floor(x))%n, int(np.floor(y))%n, int(np.floor(z))%n
        i1, j1, k1 = (i0+1)%n, (j0+1)%n, (k0+1)%n
        dx, dy, dz = x - np.floor(x), y - np.floor(y), z - np.floor(z)
        c000 = self.pressure_field[i0,j0,k0]; c100 = self.pressure_field[i1,j0,k0]
        c010 = self.pressure_field[i0,j1,k0]; c110 = self.pressure_field[i1,j1,k0]
        c001 = self.pressure_field[i0,j0,k1]; c101 = self.pressure_field[i1,j0,k1]
        c011 = self.pressure_field[i0,j1,k1]; c111 = self.pressure_field[i1,j1,k1]
        return float(
            (c000*(1-dx)+c100*dx)*(1-dy)*(1-dz) +
            (c010*(1-dx)+c110*dx)*dy*(1-dz) +
            (c001*(1-dx)+c101*dx)*(1-dy)*dz +
            (c011*(1-dx)+c111*dx)*dy*dz
        )

    def _build_nodes(self) -> None:
        self.nodes.clear()
        step = self.grid_size / self.map_resolution
        for ix in range(self.map_resolution):
            for iy in range(self.map_resolution):
                for iz in range(self.map_resolution):
                    x = ix * step
                    y = iy * step
                    z = iz * step
                    pressure = self._interpolate_pressure(x, y, z)
                    gradient = self._compute_gradient_at(x, y, z)
                    grad_norm = float(np.linalg.norm(gradient))
                    fractal_k = grad_norm / max(pressure, 1e-8)
                    effective_mass = pressure * fractal_k * 100.0
                    circulation = grad_norm
                    phase = (self.rng.random() * 0.1 + fractal_k) % (2 * np.pi)
                    self.nodes[(ix, iy, iz)] = FieldNode(
                        position=(ix, iy, iz),
                        coords=np.array([x, y, z]),
                        pressure=pressure,
                        gradient=gradient,
                        circulation=circulation,
                        phase=phase,
                        fractal_k=fractal_k,
                        effective_mass=effective_mass,
                    )

    def _get_neighbors(self, ix: int, iy: int, iz: int) -> List[Tuple[int, int, int]]:
        neighbors = []
        for di, dj, dk in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            ni, nj, nk = ix+di, iy+dj, iz+dk
            if (ni, nj, nk) in self.nodes:
                neighbors.append((ni, nj, nk))
        return neighbors

    def _find_runners(self) -> None:
        """
        Находит бегуны — линии минимального градиента.
        Бегун начинается в узле с низким градиентом и следует по пути наименьшего сопротивления.
        """
        self.runners.clear()
        self.transitions.clear()

        visited: set = set()
        runner_id = 0

        sorted_nodes = sorted(
            self.nodes.items(),
            key=lambda item: float(np.linalg.norm(item[1].gradient))
        )

        for (ix, iy, iz), node in sorted_nodes:
            if (ix, iy, iz) in visited:
                continue

            grad_norm = float(np.linalg.norm(node.gradient))
            if grad_norm > MIN_GRADIENT_FOR_RUNNER * 2:
                continue

            runner_nodes_forward = self._trace_runner(ix, iy, iz, visited, forward=True)
            runner_nodes_backward = self._trace_runner(ix, iy, iz, visited, forward=False)

            runner_nodes = list(reversed(runner_nodes_backward)) + [(ix, iy, iz)] + runner_nodes_forward

            seen = set()
            unique_runner = []
            for n in runner_nodes:
                if n not in seen:
                    seen.add(n)
                    unique_runner.append(n)
                    visited.add(n)

            if len(unique_runner) >= 3:
                runner = Runner(
                    id=runner_id,
                    nodes=unique_runner,
                    length=len(unique_runner) * (self.grid_size / self.map_resolution),
                    mean_gradient=float(np.mean([
                        np.linalg.norm(self.nodes[n].gradient)
                        for n in unique_runner
                    ])),
                )
                self.runners.append(runner)
                runner_id += 1

        node_runners: Dict[Tuple, List[int]] = {}
        for runner in self.runners:
            for node_pos in runner.nodes:
                if node_pos not in node_runners:
                    node_runners[node_pos] = []
                node_runners[node_pos].append(runner.id)

        for pos, runner_ids in node_runners.items():
            if len(runner_ids) >= 2:
                self.transitions.append(Transition(
                    position=pos,
                    runners=runner_ids,
                ))

    def _trace_runner(
        self, start_ix: int, start_iy: int, start_iz: int,
        visited: set, forward: bool = True
    ) -> List[Tuple[int, int, int]]:
        """Трассирует бегун в одном направлении."""
        path = []
        current = (start_ix, start_iy, start_iz)
        steps = 0
        max_steps = self.map_resolution * 3

        while steps < max_steps:
            curr_node = self.nodes[current]
            neighbors = self._get_neighbors(*current)
            if not neighbors:
                break
            unvisited = [n for n in neighbors if n not in visited and n not in path]
            if not unvisited:
                break
            best_neighbor = min(
                unvisited,
                key=lambda n: float(np.linalg.norm(self.nodes[n].gradient))
            )
            best_grad = float(np.linalg.norm(self.nodes[best_neighbor].gradient))
            curr_grad = float(np.linalg.norm(curr_node.gradient))
            if best_grad > curr_grad * 2.0:
                break
            path.append(best_neighbor)
            current = best_neighbor
            steps += 1

        return path

    def add_gate(self, position: np.ndarray, mass: float = 30.0) -> None:
        """Добавляет искусственные Врата."""
        self.sources.append({
            'position': position.astype(float),
            'mass': mass,
        })
        self._build_pressure_field()
        self._build_nodes()
        self._find_runners()
        logger.info("Врата добавлены в %s, масса=%.1f", position, mass)

    def get_node(self, ix: int, iy: int, iz: int) -> Optional[FieldNode]:
        return self.nodes.get((ix, iy, iz))

    def get_runner(self, runner_id: int) -> Optional[Runner]:
        for runner in self.runners:
            if runner.id == runner_id:
                return runner
        return None

    def export_to_dict(self) -> Dict:
        nodes_dict = {}
        for (ix, iy, iz), node in self.nodes.items():
            nodes_dict[f"{ix},{iy},{iz}"] = {
                'coords': node.coords.tolist(),
                'pressure': node.pressure,
                'gradient': node.gradient.tolist(),
                'circulation': node.circulation,
                'phase': node.phase,
                'fractal_k': node.fractal_k,
                'effective_mass': node.effective_mass,
            }
        runners_dict = [{
            'id': r.id,
            'nodes': [f"{n[0]},{n[1]},{n[2]}" for n in r.nodes],
            'length': r.length,
            'mean_gradient': r.mean_gradient,
        } for r in self.runners]
        transitions_dict = [{
            'position': f"{t.position[0]},{t.position[1]},{t.position[2]}",
            'runners': t.runners,
        } for t in self.transitions]

        return {
            'grid_size': self.grid_size,
            'map_resolution': self.map_resolution,
            'n_sources': len(self.sources),
            'n_nodes': len(self.nodes),
            'n_runners': len(self.runners),
            'n_transitions': len(self.transitions),
            'nodes': nodes_dict,
            'runners': runners_dict,
            'transitions': transitions_dict,
        }

    def save(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(self.export_to_dict(), f, indent=2)
        logger.info("Карта сохранена в %s", filepath)

    @classmethod
    def load(cls, filepath: str) -> FieldMap3D:
        with open(filepath) as f:
            data = json.load(f)
        sources = [{
            'position': np.array([data['grid_size']/2]*3),
            'mass': 100.0,
        }] * data['n_sources']
        obj = cls.__new__(cls)
        obj.grid_size = data['grid_size']
        obj.map_resolution = data['map_resolution']
        obj.sources = sources
        obj.rng = np.random.RandomState(42)
        obj.pressure_field = np.full((obj.grid_size, obj.grid_size, obj.grid_size), BACKGROUND_PRESSURE)
        obj._build_pressure_field()
        obj.nodes = {}
        for key, node_data in data['nodes'].items():
            ix, iy, iz = map(int, key.split(','))
            obj.nodes[(ix, iy, iz)] = FieldNode(
                position=(ix, iy, iz),
                coords=np.array(node_data['coords']),
                pressure=node_data['pressure'],
                gradient=np.array(node_data['gradient']),
                circulation=node_data['circulation'],
                phase=node_data['phase'],
                fractal_k=node_data['fractal_k'],
                effective_mass=node_data['effective_mass'],
            )
        obj.runners = []
        obj.transitions = []
        obj._find_runners()
        logger.info("Карта загружена из %s", filepath)
        return obj

    def run(self, verbose: bool = True) -> Dict:
        if verbose:
            print("=" * 70)
            print("  3D-КАРТА ВИХРЕВОГО ПОЛЯ — Акт IX")
            print("=" * 70)
            print(f"  Решётка: {self.grid_size}³")
            print(f"  Узлов: {len(self.nodes)} ({self.map_resolution}³)")
            print(f"  Бегунов: {len(self.runners)}")
            print(f"  Переходов: {len(self.transitions)}")
            print(f"  Источников: {len(self.sources)}")
            if self.runners:
                lengths = [r.length for r in self.runners]
                print(f"  Средняя длина бегуна: {np.mean(lengths):.1f}")
                print(f"  Самый длинный бегун: {np.max(lengths):.1f}")
            if self.transitions:
                print(f"  Крупнейший узел: {max(len(t.runners) for t in self.transitions)} бегунов")
            print("=" * 70)
        return {
            'n_nodes': len(self.nodes),
            'n_runners': len(self.runners),
            'n_transitions': len(self.transitions),
            'has_runners': len(self.runners) > 0,
            'has_transitions': len(self.transitions) > 0,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    map1 = FieldMap3D(grid_size=32, map_resolution=24, random_seed=42)
    map1.run(verbose=True)
    map1.save("field_map_single_star.json")
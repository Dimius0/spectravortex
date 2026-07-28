"""
TEESRouter v0.46 — ATTENTION CORE EDITION
===========================================
Фокус внимания вместо равномерного поля.
K-полосы и вычисления концентрируются только там, где сложный рельеф.
"""

import numpy as np
import time
import logging
from typing import Tuple, List, Dict

logger = logging.getLogger("TEES_Attention")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

try:
    import cupy as cp
    HAS_GPU = True
except ImportError:
    HAS_GPU = False
    cp = None

# ---------------------------------------------------------------------------
class TEES_AttentionCore:
    BASE_COUPLING = np.array([
        0.259921, 0.442249, 0.709975, 0.912931, 0.148693, 0.307107, 0.518294, 0.651839,
        0.822315, 0.959920, 0.089322, 0.209579, 0.330643, 0.446273, 0.551831, 0.657378,
        0.761885, 0.867051, 0.975174, 0.075541, 0.183840, 0.286918, 0.393314, 0.497253,
        0.604512, 0.706761, 0.812413, 0.915046, 0.015973, 0.116299, 0.218563, 0.316947,
    ], dtype=np.float64)

    def __init__(
        self,
        field_size: int = 64,
        max_qubits: int = 10000,
        sub_resolution: int = 10,
        use_3d: bool = True,
        batch_size: int = 50000,
    ):
        self.field_size = field_size
        self.max_qubits = max_qubits
        self.sub_res = sub_resolution
        self.use_3d = use_3d
        self.batch_size = batch_size

        if HAS_GPU:
            self.xp = cp
            logger.info("🔥 GPU — CuPy")
        else:
            self.xp = np
            logger.info("💻 CPU NumPy")

        if self.use_3d:
            self.field = self.xp.zeros((field_size, field_size, field_size), dtype=self.xp.complex128)
            logger.info(f"3D Бочка {field_size}³ ({self.field.size} ячеек)")
        else:
            self.field = self.xp.zeros((field_size * 4, field_size * 4), dtype=self.xp.complex128)
            logger.info(f"2D Фанера {field_size * 4}²")

        # Тепловая карта внимания (0.0 = пусто, 1.0 = сложно)
        self.attention_map = np.zeros((field_size, field_size, field_size))

        self.chip_temp = 30.0
        self.entropy_balance = 0.0
        self.num_k = 32

        self._max_k_by_ram = self._calc_max_k()
        logger.info(f"🎛️  K-полосы: авто-потолок {self._max_k_by_ram} (по RAM)")

        self._initialize_resonance_field()

    # ------------------------------------------------------------------
    def _calc_max_k(self) -> int:
        try:
            import psutil
            available_mb = psutil.virtual_memory().available / (1024 * 1024)
            k_by_ram = int(available_mb * 1024 * 1024 * 0.0001 / 8)
            return max(256, min(k_by_ram, 32768))
        except ImportError:
            return 4096

    # ------------------------------------------------------------------
    def _initialize_resonance_field(self):
        if self.use_3d:
            x = self.xp.linspace(0, 4 * self.xp.pi, self.field_size)
            y = self.xp.linspace(0, 4 * self.xp.pi, self.field_size)
            z = self.xp.linspace(0, 4 * self.xp.pi, self.field_size)
            X, Y, Z = self.xp.meshgrid(x, y, z, indexing="ij")
            base = (
                self.xp.sin(X) * self.xp.cos(Y)
                + self.xp.sin(Y) * self.xp.cos(Z)
                + self.xp.sin(Z) * self.xp.cos(X)
            )
            rng = np.random.RandomState(42)
            noise = rng.normal(0, 0.1, self.field.shape).astype(np.complex128)
            if HAS_GPU:
                noise = cp.asarray(noise)
            self.field = base + 1j * noise
        else:
            x = self.xp.linspace(0, 4 * self.xp.pi, self.field_size * 4)
            y = self.xp.linspace(0, 4 * self.xp.pi, self.field_size * 4)
            X, Y = self.xp.meshgrid(x, y)
            base = self.xp.sin(X) * self.xp.cos(Y) + self.xp.sin(Y) * self.xp.cos(X)
            rng = np.random.RandomState(42)
            noise = rng.normal(0, 0.1, self.field.shape).astype(np.complex128)
            if HAS_GPU:
                noise = cp.asarray(noise)
            self.field = base + 1j * noise
        logger.info("✅ Поле готово (с модулем внимания)")

    # ------------------------------------------------------------------
    def _get_local_k_bands(self, x0, y0, z0, base_k):
        """Динамический расчёт числа полос для конкретной ячейки."""
        # Усредняем внимание по окрестности ячейки
        x_slice = slice(max(0, x0-1), min(self.field_size, x0+2))
        y_slice = slice(max(0, y0-1), min(self.field_size, y0+2))
        z_slice = slice(max(0, z0-1), min(self.field_size, z0+2))
        local_attention = np.mean(self.attention_map[x_slice, y_slice, z_slice])

        # 4 полосы минимум, до max_k при максимальном внимании
        return int(4 + local_attention * (self._max_k_by_ram - 4))

    # ------------------------------------------------------------------
    def _interpolate_field_3d_vectorized(self, points: np.ndarray) -> np.ndarray:
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        x0 = np.int32(np.floor(x))
        y0 = np.int32(np.floor(y))
        z0 = np.int32(np.floor(z))

        mask = (
            (x0 >= 0) & (x0 < self.field_size - 1) &
            (y0 >= 0) & (y0 < self.field_size - 1) &
            (z0 >= 0) & (z0 < self.field_size - 1)
        )

        fx = x - x0
        fy = y - y0
        fz = z - z0

        c000 = self.field[(x0, y0, z0)]
        c100 = self.field[(x0 + 1, y0, z0)]
        c010 = self.field[(x0, y0 + 1, z0)]
        c110 = self.field[(x0 + 1, y0 + 1, z0)]
        c001 = self.field[(x0, y0, z0 + 1)]
        c101 = self.field[(x0 + 1, y0, z0 + 1)]
        c011 = self.field[(x0, y0 + 1, z0 + 1)]
        c111 = self.field[(x0 + 1, y0 + 1, z0 + 1)]

        c00 = c000 * (1 - fx) + c100 * fx
        c01 = c001 * (1 - fx) + c101 * fx
        c10 = c010 * (1 - fx) + c110 * fx
        c11 = c011 * (1 - fx) + c111 * fx

        c0 = c00 * (1 - fy) + c10 * fy
        c1 = c01 * (1 - fy) + c11 * fy

        result = c0 * (1 - fz) + c1 * fz
        result[~mask] = 0.0 + 0.0j

        if HAS_GPU:
            result = cp.asnumpy(result)
        return result

    # ------------------------------------------------------------------
    def _reinforce_field_along_path(self, path_points: np.ndarray, quality: float):
        quality = min(quality, 1.0)
        x, y, z = path_points[:, 0], path_points[:, 1], path_points[:, 2]
        x0 = np.int32(np.floor(x))
        y0 = np.int32(np.floor(y))
        z0 = np.int32(np.floor(z))

        mask = (
            (x0 >= 0) & (x0 < self.field_size - 1) &
            (y0 >= 0) & (y0 < self.field_size - 1) &
            (z0 >= 0) & (z0 < self.field_size - 1)
        )

        boost = quality * 0.05 * np.exp(1j * np.angle(self.field[x0[mask], y0[mask], z0[mask]]))
        self.field[x0[mask], y0[mask], z0[mask]] += boost

    # ------------------------------------------------------------------
    def _scan_attention(self, positions: Dict, edges: List):
        """Быстрый пре-скан: где качество низкое — туда внимание."""
        logger.info("🔍 Сканирование внимания...")
        self.attention_map.fill(0.0)

        # Анализируем только каждый 10-й участок для скорости
        sample_edges = edges[::max(1, len(edges)//5000)]

        for u, v in sample_edges:
            p1 = np.array(positions[u])
            p2 = np.array(positions[v])
            dist = float(np.linalg.norm(p1 - p2))
            segments = max(1, int(dist * self.sub_res * 0.1))  # грубая оценка
            t = np.linspace(0, 1, segments).reshape(-1, 1)
            points = p1.reshape(1, 3) + t * (p2 - p1).reshape(1, 3)

            field_vals = self._interpolate_field_3d_vectorized(points)
            quality = float(np.clip(np.mean(np.abs(field_vals)), 0.0, 1.0))

            if quality < 0.8:  # Сложный участок!
                x0 = np.int32(np.floor(points[:, 0]))
                y0 = np.int32(np.floor(points[:, 1]))
                z0 = np.int32(np.floor(points[:, 2]))
                valid = (
                    (x0 >= 0) & (x0 < self.field_size) &
                    (y0 >= 0) & (y0 < self.field_size) &
                    (z0 >= 0) & (z0 < self.field_size)
                )
                # Усиливаем внимание к этим ячейкам
                np.add.at(self.attention_map, (x0[valid], y0[valid], z0[valid]), 0.15)

        np.clip(self.attention_map, 0.0, 1.0, out=self.attention_map)
        attention_coverage = np.mean(self.attention_map > 0.1) * 100
        logger.info(f"  Зон внимания: {attention_coverage:.1f}% объёма")

    # ------------------------------------------------------------------
    def _quantum_resonance_path_vectorized(
        self, pos_u: np.ndarray, pos_v: np.ndarray
    ) -> Tuple[float, float, np.ndarray]:
        dist = float(np.linalg.norm(pos_u - pos_v))
        segments = max(1, int(dist * self.sub_res))

        t = np.linspace(0, 1, segments).reshape(-1, 1)
        path_points = pos_u.reshape(1, 3) + t * (pos_v - pos_u).reshape(1, 3)

        field_vals = self._interpolate_field_3d_vectorized(path_points)

        total_phase = np.sum(np.angle(field_vals))
        field_strength = np.sum(np.abs(field_vals))

        avg_phase = total_phase / segments
        avg_strength = field_strength / segments

        resonance_quality = float(np.clip(np.abs(np.cos(avg_phase)) * avg_strength, 0.0, 1.0))
        return dist, resonance_quality, path_points

    # ------------------------------------------------------------------
    def _apply_entropy_cooling(self, resonance_quality: float):
        resonance_quality = min(resonance_quality, 1.0)
        coherence = resonance_quality ** 2
        heat = (1.0 - coherence) * 50.0
        cooling_applied = min(75.0, heat * 1.5)
        self.chip_temp += (heat - cooling_applied) * 0.1
        if self.chip_temp < -200:
            self.entropy_balance += (1.0 - coherence) * 10
        else:
            self.entropy_balance += 1.0 - coherence
        self.chip_temp = max(-273.15, self.chip_temp)

    # ------------------------------------------------------------------
    def generate_topology(self, num_qubits: int) -> Tuple[Dict, List]:
        rng = np.random.RandomState(42)
        positions = {}
        for i in range(num_qubits):
            if self.use_3d:
                positions[i] = (
                    rng.uniform(0, self.field_size - 1),
                    rng.uniform(0, self.field_size - 1),
                    rng.uniform(0, self.field_size - 1),
                )
            else:
                s = self.field_size * 4
                positions[i] = (rng.uniform(0, s - 1), rng.uniform(0, s - 1), 0)

        edges = []
        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                if rng.random() < 0.05:
                    edges.append((i, j))
        logger.info(f"Топология: {num_qubits} кубитов, {len(edges)} рёбер")
        return positions, edges

    # ------------------------------------------------------------------
    def run_resonance(self, positions: Dict, edges: List, epochs: int = 3) -> Dict:
        start_time = time.time()

        # 1. Фаза сканирования
        self._scan_attention(positions, edges)

        success_count = 0
        total_quality = 0.0

        for epoch in range(epochs):
            batch_quality = 0.0
            batch_success = 0

            for i in range(0, len(edges), self.batch_size):
                batch = edges[i:i + self.batch_size]

                for u, v in batch:
                    p1 = np.array(positions[u])
                    p2 = np.array(positions[v])
                    dist, quality, path_points = self._quantum_resonance_path_vectorized(p1, p2)

                    if quality > 0.7:
                        self._reinforce_field_along_path(path_points, quality)
                        batch_success += 1
                    batch_quality += quality

            avg_quality = batch_quality / max(1, len(edges))
            success_rate = batch_success / max(1, len(edges))
            total_quality = avg_quality
            success_count = batch_success

            logger.info(f"  Эпоха {epoch+1}: успех {success_rate:.2%}, "
                       f"качество {avg_quality:.4f}")
            self._apply_entropy_cooling(avg_quality)

        elapsed = time.time() - start_time

        Q = total_quality
        T = elapsed
        M = self.field.nbytes / (1024 * 1024)
        dS = abs(self.entropy_balance)
        TES = round((Q * len(edges)) / (T * M * max(dS, 0.01)), 2) if T > 0 else 0

        return {
            "total_edges": len(edges),
            "success_rate": success_count / max(1, len(edges)),
            "avg_resonance": total_quality,
            "routing_time": elapsed,
            "chip_temp": self.chip_temp,
            "entropy_balance": self.entropy_balance,
            "k_bands_used": self.num_k,
            "memory_mb": M,
            "TES": TES,
            "gpu_used": HAS_GPU,
        }


# ===========================================================================
def flight_test():
    logger.info("=" * 50)
    logger.info("🚀 TEESRouter v0.46 — Attention Core")
    logger.info("=" * 50)

    tees = TEES_AttentionCore(
        field_size=64,
        max_qubits=10000,
        sub_resolution=10,
        use_3d=True,
        batch_size=50000,
    )

    for q in [100, 500, 1000, 2000, 5000, 10000]:
        logger.info(f"\n--- Тест: {q} кубитов ---")
        pos, edges = tees.generate_topology(q)
        result = tees.run_resonance(pos, edges, epochs=3)
        logger.info(f"✅ ИТОГ: TES={result['TES']} | "
                   f"Успех {result['success_rate']:.2%} | "
                   f"🌡️ {result['chip_temp']:.1f}°C | "
                   f"⏱️ {result['routing_time']:.1f}сек")

    logger.info("\n" + "=" * 50)
    logger.info("ГОТОВО. Внимание сфокусировано.")
    logger.info("=" * 50)


if __name__ == "__main__":
    flight_test()
# tees_seed_distributor.py
# 🌱 Исправленная версия

import time
import json
import hashlib
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from tees_core_tees import (
    tees_recursive_vortex,
    tees_triad_collapse,
    tees_sign,
    tees_verify,
    VERSION
)

from tees_knowledge_engine_v5_6 import (
    seed_to_vortex,
    compute_topological_charge,
    tees_shift,
    VortexConfig,
    vmmp_entropy
)

from tees_beacon_tees import FractalMemory


@dataclass
class SeedPiece:
    """🌰 Кусок семени — вихрь в TEES-пространстве."""
    piece_id: str
    data: bytes
    index: int
    size: int
    seed_hash: str
    seed_hash_bytes: bytes  # ← НОВОЕ: полный hash для верификации
    creator_address: str
    
    tees_signature: str = ''
    vortex_hash: bytes = b''
    triad_hash: bytes = b''
    topological_charge: float = 0.0
    
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            'piece_id': self.piece_id,
            'index': self.index,
            'size': self.size,
            'seed_hash': self.seed_hash,
            'creator': self.creator_address,
            'tees_signature': self.tees_signature,
            'topological_charge': self.topological_charge,
            'created_at': self.created_at
        }


class SeedDistributor:
    """🌱 Распределённая раздача семян на TEES-физике."""
    
    def __init__(self, beacon=None):
        self.beacon = beacon
        self.pieces: Dict[str, SeedPiece] = {}
        self.seed_manifest: Dict[str, Dict] = {}
        self.planted_seeds: Dict[str, Dict] = {}
        
        self.fractal_memory = FractalMemory(max_level_0=100)
        self.vortex_config = VortexConfig(grid_size=16)
        
        self.PIECE_SIZE = 1024
        self.MAX_STORED_PIECES = 100
        self.VORTEX_DEPTH = 3
        
        if beacon:
            self.init_seed = beacon.init_seed
        else:
            self.init_seed = hashlib.sha256(b"forest_seed").digest()
        
        self.stats = {
            'seeds_created': 0,
            'pieces_stored': 0,
            'pieces_verified': 0,
            'pieces_rejected': 0,
            'seeds_collected': 0,
            'verification_failures': 0
        }
    
    def create_seed(self, seed_data: bytes, creator_address: str = '') -> Dict:
        """🌰 Создать семя из данных."""
        # Полный hash (32 байта)
        seed_hash_bytes = tees_recursive_vortex(
            seed_data, 
            self.init_seed, 
            self.VORTEX_DEPTH
        )
        # Короткий hash для отображения
        seed_hash = seed_hash_bytes.hex()[:32]
        
        creation_time = time.time()
        pieces_info = []
        
        for i in range(0, len(seed_data), self.PIECE_SIZE):
            piece_data = seed_data[i:i + self.PIECE_SIZE]
            piece_index = i // self.PIECE_SIZE
            
            # Данные для вихря: piece_data + index + ПОЛНЫЙ seed_hash
            vortex_input = piece_data + piece_index.to_bytes(4, 'big') + seed_hash_bytes
            
            piece_id_bytes = tees_recursive_vortex(
                vortex_input,
                self.init_seed,
                self.VORTEX_DEPTH
            )
            piece_id = piece_id_bytes.hex()[:32]
            
            signature = tees_sign(
                piece_data + piece_index.to_bytes(4, 'big'),
                self.init_seed
            )
            
            triad_hash = tees_triad_collapse(piece_id_bytes)
            
            vortex = seed_to_vortex(
                int.from_bytes(piece_id_bytes[:8], 'big'),
                self.vortex_config
            )
            charge = compute_topological_charge(vortex)
            
            piece = SeedPiece(
                piece_id=piece_id,
                data=piece_data,
                index=piece_index,
                size=len(piece_data),
                seed_hash=seed_hash,
                seed_hash_bytes=seed_hash_bytes,  # ← Сохраняем полный hash
                creator_address=creator_address,
                tees_signature=signature,
                vortex_hash=piece_id_bytes,
                triad_hash=triad_hash,
                topological_charge=charge
            )
            
            self.pieces[piece_id] = piece
            pieces_info.append(piece.to_dict())
            self.stats['pieces_stored'] += 1
        
        manifest = {
            'seed_hash': seed_hash,
            'total_pieces': len(pieces_info),
            'piece_ids': [p['piece_id'] for p in pieces_info],
            'total_size': len(seed_data),
            'created_at': creation_time,
            'creator': creator_address,
            'pieces': pieces_info,
            'version': VERSION
        }
        
        self.seed_manifest[seed_hash] = manifest
        self.stats['seeds_created'] += 1
        
        self.fractal_memory.add({
            'type': 'seed_created',
            'seed_hash': seed_hash,
            'pieces': len(pieces_info),
            'creator': creator_address,
            'time': creation_time
        })
        
        return manifest
    
    def verify_piece(self, piece_id: str, piece_data: bytes, 
                    node_address: str = '') -> Dict:
        """🔍 Верификация куска через TEES-физику."""
        result = {
            'piece_id': piece_id,
            'verified': False,
            'checks': {},
            'timestamp': time.time()
        }
        
        piece = self.pieces.get(piece_id)
        if not piece:
            result['error'] = 'Кусок не найден'
            return result
        
        # Проверка 1: TEES-подпись
        try:
            expected_signature = piece.tees_signature
            actual_signature = tees_sign(
                piece_data + piece.index.to_bytes(4, 'big'),
                self.init_seed
            )
            result['checks']['signature'] = (expected_signature == actual_signature)
        except Exception as e:
            result['checks']['signature'] = False
            result['checks']['signature_error'] = str(e)
        
        # Проверка 2: Вихревой хеш (ИСПРАВЛЕНО!)
        try:
            # Используем те же данные, что и при создании
            vortex_input = piece_data + piece.index.to_bytes(4, 'big') + piece.seed_hash_bytes
            vortex_hash = tees_recursive_vortex(
                vortex_input,
                self.init_seed,
                self.VORTEX_DEPTH
            )
            result['checks']['vortex'] = (vortex_hash == piece.vortex_hash)
        except Exception as e:
            result['checks']['vortex'] = False
            result['checks']['vortex_error'] = str(e)
        
        # Проверка 3: Топологический заряд
        try:
            vortex = seed_to_vortex(
                int.from_bytes(piece.vortex_hash[:8], 'big'),
                self.vortex_config
            )
            charge = compute_topological_charge(vortex)
            result['checks']['charge'] = (abs(charge - piece.topological_charge) < 0.001)
        except Exception as e:
            result['checks']['charge'] = False
            result['checks']['charge_error'] = str(e)
        
        all_checks = list(result['checks'].values())
        result['verified'] = all(all_checks) if all_checks else False
        
        if result['verified']:
            self.stats['pieces_verified'] += 1
        else:
            self.stats['pieces_rejected'] += 1
            self.stats['verification_failures'] += 1
        
        return result
    
    def collect_seed(self, piece_ids: List[str]) -> Optional[bytes]:
        """🌟 Собрать семя из кусков."""
        pieces = []
        
        for pid in piece_ids:
            piece = self.pieces.get(pid)
            if not piece:
                print(f"❌ Кусок {pid} отсутствует")
                return None
            
            verification = self.verify_piece(pid, piece.data)
            if not verification['verified']:
                print(f"🚨 Кусок {pid} не прошёл верификацию!")
                print(f"   Проверки: {verification['checks']}")
                return None
            
            pieces.append(piece)
        
        pieces.sort(key=lambda p: p.index)
        seed_data = b''.join(p.data for p in pieces)
        self.stats['seeds_collected'] += 1
        
        return seed_data
    
    def get_germination_progress(self, piece_ids: List[str]) -> Dict:
        """🌱 Прогресс прорастания семени."""
        total = len(piece_ids)
        collected = 0
        verified = 0
        
        for pid in piece_ids:
            piece = self.pieces.get(pid)
            if piece:
                collected += 1
                verification = self.verify_piece(pid, piece.data)
                if verification['verified']:
                    verified += 1
        
        progress = verified / total if total > 0 else 0
        
        if progress < 0.25:
            stage = "🌰 Семя спит..."
        elif progress < 0.5:
            stage = "🌱 Росток пробивается..."
        elif progress < 0.75:
            stage = "🌿 Молодое дерево растёт..."
        elif progress < 1.0:
            stage = "🌳 Дерево почти выросло!"
        else:
            stage = "🌟 Дерево выросло! Лес стал больше!"
        
        return {
            'collected': collected,
            'verified': verified,
            'total': total,
            'progress': round(progress * 100, 1),
            'stage': stage,
            'missing': [pid for pid in piece_ids if pid not in self.pieces]
        }
    
    def get_health(self) -> Dict:
        """🏥 Здоровье распределённого хранилища."""
        return {
            'total_pieces': len(self.pieces),
            'total_seeds': len(self.seed_manifest),
            'stats': self.stats,
            'fractal_depth': self.fractal_memory.get_depth(),
            'fractal_memory': self.fractal_memory.get_total_memory(),
            'rejection_rate': round(
                self.stats['pieces_rejected'] / max(1, self.stats['pieces_verified'] + self.stats['pieces_rejected']) * 100, 1
            )
        }
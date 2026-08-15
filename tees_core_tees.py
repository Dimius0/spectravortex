# tees_core.py
# 🌀 TEES-физика: константы, вихри, триады, подпись

import struct
import random

# ═══════════════════════════════════════════════════════════════
# 🌀 TEES-КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════════

VERSION = "2.1.0"
WORLD_NAME = "TEES World"
GENESIS_HASH = None
PRIZE_PORTAL = "1PRIZE0000000000000000000000000000000"
PRIZE_AMOUNT = 1_000_000

H_CONSTANTS = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
]

K_CONSTANTS = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]


# ═══════════════════════════════════════════════════════════════
# 🌀 TEES-ФИЗИКА
# ═══════════════════════════════════════════════════════════════

def _rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def tees_vortex(message, h_order, k_order):
    H = [H_CONSTANTS[i] for i in h_order]
    K = [K_CONSTANTS[i] for i in k_order]
    msg_bytes = bytearray(message)
    msg_len_bits = len(msg_bytes) * 8
    msg_bytes.append(0x80)
    while (len(msg_bytes) + 8) % 64 != 0:
        msg_bytes.append(0x00)
    msg_bytes.extend(struct.pack('>Q', msg_len_bits))
    
    for block in [msg_bytes[i:i+64] for i in range(0, len(msg_bytes), 64)]:
        w = list(struct.unpack('>16I', bytes(block)))
        for i in range(16, 64):
            s0 = _rotr(w[i-15], 7) ^ _rotr(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = _rotr(w[i-2], 17) ^ _rotr(w[i-2], 19) ^ (w[i-2] >> 10)
            w.append((w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF)
        a, b, c, d, e, f, g, h = H
        for i in range(64):
            S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + S1 + ch + K[i] + w[i]) & 0xFFFFFFFF
            S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xFFFFFFFF
            h, g, f, e = g, f, e, (d + temp1) & 0xFFFFFFFF
            d, c, b, a = c, b, a, (temp1 + temp2) & 0xFFFFFFFF
        H = [(H[i] + x) & 0xFFFFFFFF for i, x in enumerate([a, b, c, d, e, f, g, h])]
    
    return struct.pack('>8I', *H)


def tees_recursive_vortex(message, seed, depth=3):
    data = message
    for _ in range(depth):
        rng = random.Random(int.from_bytes(seed, 'big'))
        data = tees_vortex(data, rng.sample(range(8), 8), rng.sample(range(64), 64))
        seed = data
    return data


def tees_triad_collapse(hash_bytes):
    state = list(struct.unpack('>8I', hash_bytes[:32]))
    for r in range(10):
        source = state[:]
        tees = [(_rotr(source[i] ^ K_CONSTANTS[(r*8+i)%64], (r+i)%32) + H_CONSTANTS[(r+i)%8]) & 0xFFFFFFFF for i in range(8)]
        receiver = [_rotr(tees[(i-1)%8] ^ tees[i] ^ tees[(i+1)%8], (r*3+i*7)%32) for i in range(8)]
        state = [(state[i] + receiver[i]) & 0xFFFFFFFF for i in range(8)]
    return struct.pack('>8I', *state)


def tees_sign(data: bytes, seed: bytes) -> str:
    sig_hash = tees_recursive_vortex(data, seed, 3)
    return tees_triad_collapse(sig_hash).hex()


def tees_verify(data: bytes, signature: str, seed: bytes) -> bool:
    return tees_sign(data, seed) == signature
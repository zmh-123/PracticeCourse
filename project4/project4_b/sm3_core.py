"""
SM3 核心实现，支持：
- 自定义初始向量（IV）
- 传入 total_bytes_prefix 以便进行“长度扩展攻击”的连续压缩

所有输入/输出均使用 Python 内置类型（bytes/str/int）。
"""
from __future__ import annotations
from typing import List, Optional, Tuple

# GB/T 32905-2016（SM3）中的默认初始向量
IV_DEFAULT: List[int] = [
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E,
]

# T_j 常量（32 位）
T_J: List[int] = [0x79CC4519] * 16 + [0x7A879D8A] * 48

MASK_32 = 0xFFFFFFFF

def rotl32(x: int, n: int) -> int:
    """32 位循环左移。"""
    n = n & 31
    return ((x << n) & MASK_32) | ((x & MASK_32) >> (32 - n))

def P0(x: int) -> int:
    """P0 线性变换。"""
    return x ^ rotl32(x, 9) ^ rotl32(x, 17)

def P1(x: int) -> int:
    """P1 线性变换。"""
    return x ^ rotl32(x, 15) ^ rotl32(x, 23)

def FF(x: int, y: int, z: int, j: int) -> int:
    """布尔函数 FF。"""
    if 0 <= j <= 15:
        return x ^ y ^ z
    return (x & y) | (x & z) | (y & z)

def GG(x: int, y: int, z: int, j: int) -> int:
    """布尔函数 GG。"""
    if 0 <= j <= 15:
        return x ^ y ^ z
    return (x & y) | ((~x) & z)

def _bytes_to_u32_be(b: bytes, offset: int) -> int:
    """大端字节序读取 32 位无符号整数。"""
    return (
        (b[offset] << 24) | (b[offset + 1] << 16) | (b[offset + 2] << 8) | b[offset + 3]
    )

def _u32_to_bytes_be(x: int) -> bytes:
    """32 位无符号整数按大端编码为 4 字节。"""
    return bytes([(x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, x & 0xFF])

def _pad_message(total_len_bytes_before_padding: int) -> bytes:
    """根据 SM3 规则生成填充字节：先 0x80，再若干 0x00，使长度模 64 为 56，最后拼接 64 位消息比特长度（大端）。"""
    bit_len = total_len_bytes_before_padding * 8
    # 追加 0x80
    pad = bytearray()
    pad.append(0x80)
    # 用 0x00 填充至 (len + 1 + k) % 64 == 56
    new_len = (total_len_bytes_before_padding + 1)
    k = (56 - (new_len % 64)) % 64
    pad.extend(b"\x00" * k)
    # 追加 64 位大端比特长度
    pad.extend(bit_len.to_bytes(8, byteorder="big"))
    return bytes(pad)

def _message_blocks(msg: bytes) -> List[bytes]:
    """将消息按 64 字节切分为分组。"""
    assert len(msg) % 64 == 0
    return [msg[i:i+64] for i in range(0, len(msg), 64)]

def _compress(v: List[int], block: bytes) -> List[int]:
    """压缩函数 CF，对单个 512-bit 分组进行消息扩展与 64 轮迭代。"""
    # 消息扩展
    W = [0] * 68
    W1 = [0] * 64
    for j in range(16):
        W[j] = _bytes_to_u32_be(block, j * 4)
    for j in range(16, 68):
        W[j] = (P1(W[j-16] ^ W[j-9] ^ rotl32(W[j-3], 15)) ^ rotl32(W[j-13], 7) ^ W[j-6]) & MASK_32
    for j in range(64):
        W1[j] = (W[j] ^ W[j+4]) & MASK_32

    A, B, C, D, E, F, G, H = v

    for j in range(64):
        SS1 = rotl32(((rotl32(A, 12) + E + rotl32(T_J[j], j)) & MASK_32), 7)
        SS2 = SS1 ^ rotl32(A, 12)
        TT1 = (FF(A, B, C, j) + D + SS2 + W1[j]) & MASK_32
        TT2 = (GG(E, F, G, j) + H + SS1 + W[j]) & MASK_32
        D = C
        C = rotl32(B, 9)
        B = A
        A = TT1
        H = G
        G = rotl32(F, 19)
        F = E
        E = P0(TT2)

    return [a ^ b for a, b in zip([A, B, C, D, E, F, G, H], v)]

def sm3_hash(data: bytes, iv: Optional[List[int]] = None, total_bytes_prefix: int = 0) -> str:
    """
    计算 SM3 摘要。
    - data：本次要处理的数据（bytes）
    - iv：可选初始向量（8 个 32 位无符号整数组成）。缺省使用标准 IV。
    - total_bytes_prefix：在本次 data 之前已经“视为参与哈希”的总字节数（用于长度扩展场景，影响最终填充中的长度域）。
    返回：32 字节（256 bit）摘要的十六进制小写字符串。
    """
    if iv is None:
        v = IV_DEFAULT.copy()
    else:
        if len(iv) != 8:
            raise ValueError("iv 必须为 8 个 32 位无符号整数")
        v = [x & MASK_32 for x in iv]

    # 构造当前回合的完整输入：data || pad(total_bytes_prefix + len(data))
    total_len_before_pad = total_bytes_prefix + len(data)
    pad = _pad_message(total_len_before_pad)
    full = data + pad

    for block in _message_blocks(full):
        v = _compress(v, block)

    digest_bytes = b''.join(_u32_to_bytes_be(x) for x in v)
    return digest_bytes.hex()

def parse_digest_to_iv(digest_hex: str) -> List[int]:
    """将 64 位十六进制 SM3 摘要解析为 8×32 位（大端）的 IV，用于继续压缩。"""
    if len(digest_hex) != 64:
        raise ValueError("SM3 摘要长度必须为 64 个十六进制字符")
    b = bytes.fromhex(digest_hex)
    return [_bytes_to_u32_be(b, i*4) for i in range(8)]

def sm3_pad_bytes_for_len(total_len_bytes: int) -> bytes:
    """给定消息“未填充前”的字节长度，返回对应的 SM3 填充字节序列。"""
    return _pad_message(total_len_bytes)
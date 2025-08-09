"""
SM3 长度扩展攻击演示
流程：
1) 模拟受害者存在未知前缀密钥 S（攻击者只知道 S 的长度），受害者计算 H = SM3(S || M)
2) 攻击者仅利用 |S| 与已知消息 M，构造与受害者相同的填充 pad
3) 以旧摘要 H 作为新的初始向量 IV，并设置 total_bytes_prefix = |S||M||pad|，继续对附加数据 M' 压缩
4) 验证 SM3(S||M||pad||M') 与攻击者计算结果一致
"""
from __future__ import annotations
import os
from typing import Tuple
from sm3_core import sm3_hash, parse_digest_to_iv, sm3_pad_bytes_for_len


def victim_oracle(secret: bytes, msg: bytes) -> str:
    """受害者接口：返回 SM3(secret || msg) 的十六进制摘要。"""
    return sm3_hash(secret + msg)


def attacker_length_extension(old_digest_hex: str, known_msg: bytes, secret_len: int, append_msg: bytes) -> Tuple[str, bytes]:
    """
    基于长度扩展的伪造：
    已知 H = SM3(secret||known_msg)、secret_len、known_msg，构造并返回：
    - forged_digest: SM3(secret||known_msg||pad||append_msg)
    - forged_suffix: pad||append_msg（应追加到 known_msg 后）
    """
    # 1) 计算受害者对 S||M 做填充时的 pad（仅依赖总长度，无需知道 S 的内容）
    total_len_before_pad = secret_len + len(known_msg)
    pad = sm3_pad_bytes_for_len(total_len_before_pad)

    # 2) 以旧摘要作为新的 IV，继续对 append_msg 进行压缩
    iv = parse_digest_to_iv(old_digest_hex)
    total_prefix = total_len_before_pad + len(pad)
    new_digest = sm3_hash(append_msg, iv=iv, total_bytes_prefix=total_prefix)

    # 伪造的后缀：pad || append_msg
    forged_suffix = pad + append_msg
    return new_digest, forged_suffix


def demo_once() -> None:
    # 模拟未知前缀（受害者持有，攻击者只知道长度）
    secret = os.urandom(16)  # 示例：随机 16 字节作为“密钥前缀”
    known_msg = b"user=alice&action=transfer&amount=100"
    append_msg = b"&amount=1000000"  # 攻击者希望追加的参数

    # 受害者计算原始摘要
    orig_digest = victim_oracle(secret, known_msg)

    # 攻击者侧：已知 orig_digest、known_msg、secret_len
    secret_len = len(secret)
    forged_digest, forged_suffix = attacker_length_extension(orig_digest, known_msg, secret_len, append_msg)

    # 受害者真实结果（用于验证攻击是否成功）
    real_digest = sm3_hash(secret + known_msg + forged_suffix)

    print("原始摘要: ", orig_digest)
    print("伪造摘要: ", forged_digest)
    print("是否一致? ", (orig_digest != forged_digest) and (forged_digest == real_digest))
    print("伪造的完整消息（十六进制）:", (known_msg + forged_suffix).hex())


if __name__ == "__main__":
    demo_once()
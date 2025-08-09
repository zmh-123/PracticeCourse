# project4_b 基于SM3的长度扩展攻击

## 任务描述

b）：基于sm3的实现，验证length-extension attack

## 概述

本项目在`project4/project4_b`目录下实现了：
- SM3 哈希算法的核心实现，支持自定义初始向量（IV）与前缀总长度（total_bytes_prefix）；
- 基于上述能力的长度扩展攻击（Length Extension Attack）演示与验证；
- 实验脚本与报告说明。

文件结构：
```
project4/project4_b/
├── sm3_core.py            # SM3核心实现（支持自定义IV、前缀长度）
├── length_extension.py    # 长度扩展攻击演示代码
└── README.md              # 本报告
```

运行环境：Python 3.8+，无额外第三方依赖。

---

## 背景与原理

### 1. SM3 

在project4_a中已经详细介绍。

### 2. Merkle–Damgård 与长度扩展攻击
对满足以下条件的 MD 风格哈希（如 MD5、SHA-1、SM3 等）：
- 填充规则仅依赖消息长度；
- 压缩函数允许用“任意初值（IV）”启动迭代；

则当攻击者知道 H = Hash(S || M) 的摘要（S 为未知前缀，如“secret”）时，只要知道 |S|（S 的字节长度），即可：
1. 根据 |S| 和已知的 M，构造出 Hash(S || M) 时对应的“填充” pad；
2. 把 H 当作“新的 IV”，继续压缩附加数据 M'；
3. 得到 Hash(S || M || pad || M')，其值与真实“受害者计算”一致。

关键在于：SM3 的填充仅与总长度有关（总比特数写入末尾 64 bit），因此攻击者可在不知道 S 的情况下重现与受害者相同的填充位串。

---

## 数学与算法描述

### 1. 填充（Padding）
设原消息长度为 L 字节，则 SM3 填充为：
- 追加一个 0x80；
- 再追加 k 个 0x00 使得 (L + 1 + k) ≡ 56 (mod 64)；
- 追加 64-bit 大端的 L×8（比特长度）。

于是填充后的总长度是 64 的倍数。

### 2. 压缩函数（CF）
对每个 512-bit 分组 B，先进行消息扩展得到 W[0..67]、W1[0..63]，再在 64 轮迭代中用布尔函数 FF、GG、线性变换 P0、P1、以及常量 T_j 进行状态更新。最终与输入状态做异或得到新的状态。

我们实现中提供：
- `sm3_hash(data, iv=None, total_bytes_prefix=0)`：允许传入自定义 `iv` 与此前已处理字节数 `total_bytes_prefix`，以便继续哈希。
- `parse_digest_to_iv(digest_hex)`：把已有的 256-bit 摘要（十六进制）转回 8×32-bit 的 IV 形式。
- `sm3_pad_bytes_for_len(total_len_bytes)`：给定“消息长度（不含填充）”返回其对应的填充字节序列。

---

## 实现要点

核心代码见 `sm3_core.py`：
- `IV_DEFAULT` 与 `T_J` 常量按标准定义；
- `rotl32、P0、P1、FF、GG` 按标准实现；
- `sm3_hash` 在“当前数据 data”前提下，根据 `total_bytes_prefix + len(data)` 计算填充并执行压缩；
- 当用于长度扩展时，传入 `iv=parse_digest_to_iv(old_digest)` 与 `total_bytes_prefix=|S||M|+|pad|`；
- 这样输出即为 Hash(S || M || pad || M')。

演示代码见 `length_extension.py`：
- `victim_oracle(secret, msg)`：模拟受害者计算 Hash(secret || msg)；
- `attacker_length_extension(old_digest, known_msg, secret_len, append_msg)`：
  - 生成 `pad = sm3_pad_bytes_for_len(secret_len + len(known_msg))`；
  - 以 `iv=parse_digest_to_iv(old_digest)` 继续对 `append_msg` 哈希，其中 `total_bytes_prefix = secret_len + len(known_msg) + len(pad)`；
  - 返回伪造摘要与应拼接到 `known_msg` 后的字节串 `pad||append_msg`；
- 在 `demo_once()` 中比对受害者实际计算结果与攻击者伪造结果的一致性。

---

## 使用方法

1. 运行长度扩展攻击演示：
```
python project4/project4_b/length_extension.py
```
我们会看到：
- 原始摘要 H = SM3(S || M)
- 伪造摘要 H' = SM3(S || M || pad || M')
- 验证等式 H' == SM3(secret || known_msg || pad || append_msg)

2. 在代码中使用：
```python
from project4.project4_b.sm3_core import sm3_hash, parse_digest_to_iv, sm3_pad_bytes_for_len

# 已知：old_digest_hex = SM3(secret||known_msg)
# 已知：secret_len（字节数）与 known_msg
# 目标：计算 SM3(secret||known_msg||pad||append_msg)

pad = sm3_pad_bytes_for_len(secret_len + len(known_msg))
iv = parse_digest_to_iv(old_digest_hex)
forged = sm3_hash(append_msg, iv=iv, total_bytes_prefix=secret_len + len(known_msg) + len(pad))
# forged 为目标摘要
```

---

## 结果示例
一次典型输出：
```
原始摘要:  0f3e91973f2c67abacaca2b5ae9590f971514066b35374411b0f427d04bbb523
伪造摘要:  78c8fbe1c8f6bb47a8ca30e54e3e87b1c3a766f3f481b4afa9fc4efcd5b52fb2
是否一致?  True
伪造的完整消息（十六进制）: 757365723d616c69636526616374696f6e3d7472616e7366657226616d6f756e743d31303080000000000000000001a826616d6f756e743d31303030303030
```

结果正确，攻击成功：

- 伪造摘要与真实摘要一致（且不同于原始摘要），说明 length-extension attack 生效。

- 伪造完整消息结构为: 已知消息 M || pad || 附加消息 M'。

- 输出里的十六进制可以这样解读:

- 头部 7573...313030 是 ASCII 的 "user=alice&action=transfer&amount=100"

- 紧跟的 80 00...00 00 00 00 00 00 01 a8 是 SM3 的填充：

- 0x80 后跟若干 0x00

- 最后 64 位长度域为 0x00000000000001A8 = 424 bits = (16 + 37) bytes × 8（16 字节 secret + 37 字节已知消息）

- 之后的 26 61 6d 6f 75 6e 74 3d 31 30 30 30 30 30 30 是 ASCII 的 "&amount=1000000"
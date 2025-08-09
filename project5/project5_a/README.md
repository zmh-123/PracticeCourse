# project5_a SM2的软件实现优化

## 项目任务概述

a). 考虑到SM2用C 语言来做比较复杂，大家看可以考虑用python来做 sm2的 基础实现以及各种算法的改进尝试

## 1. 数学基础

### 1.1 椭圆曲线定义

SM2使用的椭圆曲线方程为：
```
y² = x³ + ax + b (mod p)
```

其中：
- p = 2^256 - 2^224 - 2^96 + 2^64 - 1 (素数)
- a = -3
- b = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
- 基点G = (Gx, Gy)
- 阶n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123

### 1.2 椭圆曲线运算

#### 点加法
给定两点P₁(x₁, y₁)和P₂(x₂, y₂)，计算P₃ = P₁ + P₂：

当P₁ ≠ P₂时：
```
λ = (y₂ - y₁) / (x₂ - x₁) (mod p)
x₃ = λ² - x₁ - x₂ (mod p)
y₃ = λ(x₁ - x₃) - y₁ (mod p)
```

当P₁ = P₂时（倍点）：
```
λ = (3x₁² + a) / (2y₁) (mod p)
x₃ = λ² - 2x₁ (mod p)
y₃ = λ(x₁ - x₃) - y₁ (mod p)
```

#### 标量乘法
计算kP，其中k是标量，P是椭圆曲线上的点：
```
kP = P + P + ... + P (k次)
```

## 2. SM2算法原理

### 2.1 密钥生成
1. 随机选择私钥d ∈ [1, n-1]
2. 计算公钥P = dG

### 2.2 加密算法
输入：明文M，公钥P
输出：密文C = (C₁, C₂, C₃)

1. 随机选择k ∈ [1, n-1]
2. 计算C₁ = kG
3. 计算kP = (x₂, y₂)
4. 计算t = KDF(x₂ || y₂, klen)
5. 计算C₂ = M ⊕ t
6. 计算C₃ = Hash(x₂ || M || y₂)

### 2.3 解密算法
输入：密文C = (C₁, C₂, C₃)，私钥d
输出：明文M

1. 计算dC₁ = (x₂, y₂)
2. 计算t = KDF(x₂ || y₂, klen)
3. 计算M = C₂ ⊕ t
4. 验证Hash(x₂ || M || y₂) = C₃

### 2.4 密钥派生函数KDF
```
KDF(Z, klen):
    ct = 1
    k = ""
    for i = 1 to ceil(klen/256):
        k = k || Hash(Z || ct)
        ct = ct + 1
    return k[1:klen]
```

## 3. 优化技术

### 3.1 Jacobian坐标系统

#### 3.1.1 坐标转换
仿射坐标(x, y)转换为Jacobian坐标(X, Y, Z)：
```
X = x
Y = y
Z = 1
```

Jacobian坐标转换为仿射坐标：
```
x = X/Z² (mod p)
y = Y/Z³ (mod p)
```

#### 3.1.2 Jacobian坐标下的点运算

**倍点运算**：
```
X₃ = (3X₁² + aZ₁⁴)² - 8X₁Y₁² (mod p)
Y₃ = (3X₁² + aZ₁⁴)(4X₁Y₁² - X₃) - 8Y₁⁴ (mod p)
Z₃ = 2Y₁Z₁ (mod p)
```

**点加法运算**（混合坐标系）：
```
U₁ = X₁Z₂² (mod p)
U₂ = X₂Z₁² (mod p)
S₁ = Y₁Z₂³ (mod p)
S₂ = Y₂Z₁³ (mod p)

H = U₂ - U₁ (mod p)
r = S₂ - S₁ (mod p)

X₃ = r² - H³ - 2U₁H² (mod p)
Y₃ = r(U₁H² - X₃) - S₁H³ (mod p)
Z₃ = HZ₁Z₂ (mod p)
```

**优势**：
- 避免模逆运算，提高效率
- 减少模乘运算次数

### 3.2 滑动窗口法

#### 3.2.1 算法原理
将标量k表示为w位窗口：
```
k = (kₙ₋₁...k₀)₂
```

预计算点表：
```
P[1] = P
P[3] = 3P
P[5] = 5P
...
P[2^w-1] = (2^w-1)P
```

#### 3.2.2 算法实现
```python
def window_mult_point(P, k, w, p, a):
    # 预计算点表
    points = precompute_points(P, w, p, a)
    
    # 滑动窗口计算
    result = None
    for i in range(0, len(k_bits), w):
        window = k_bits[i:i+w]
        window_val = int(window, 2)
        
        if result is None:
            result = points[window_val]
        else:
            # 左移w位
            for _ in range(w):
                result = double_point(result, p, a)
            # 加上窗口值对应的点
            result = add_point(result, points[window_val], p, a)
    
    return result
```

**复杂度分析**：
- 预计算：2^(w-1) - 1次点加法
- 标量乘法：约n/w次倍点 + n/w次点加法
- 总复杂度：O(n/w)

### 3.3 NAF（Non-Adjacent Form）表示

#### 3.3.1 NAF定义
NAF是一种特殊的二进制表示，其中任意两个相邻位不能同时为1：
```
k = Σ(i=0 to n-1) k_i × 2^i
其中 k_i ∈ {-1, 0, 1} 且 k_i × k_{i+1} = 0
```

#### 3.3.2 NAF转换算法
```python
def naf(k):
    naf_rep = []
    while k > 0:
        if k % 2 == 1:
            ki = 2 - (k % 4)  # ki ∈ {-1, 1}
            k -= ki
        else:
            ki = 0
        naf_rep.append(ki)
        k //= 2
    return naf_rep[::-1]
```

**优势**：
- 平均汉明重量约为n/3（比二进制表示少）
- 减少点加法运算次数

### 3.4 预计算优化

#### 3.4.1 固定基点预计算
对于固定的基点G，可以预计算常用倍数：
```python
def precompute_fixed_base(G, w, p, a):
    table = [None] * (1 << w)
    table[1] = G
    
    # 计算奇数倍点
    for i in range(3, 1 << w, 2):
        table[i] = add_point(table[i-2], 2*G, p, a)
    
    return table
```

#### 3.4.2 动态点预计算
对于变化的点P，在每次加密时预计算：
```python
def precompute_variable_point(P, w, p, a):
    table = [None] * (1 << w)
    table[1] = P
    
    # 计算奇数倍点
    for i in range(3, 1 << w, 2):
        table[i] = add_point(table[i-2], 2*P, p, a)
    
    return table
```

## 4. 实现架构

### 4.1 核心模块

#### 4.1.1 数据类型转换模块
```python
# 整数与字节串转换
def int_to_bytes(x, k):
    return x.to_bytes(k, 'big')

def bytes_to_int(M):
    return int.from_bytes(M, 'big')

# 比特串与字节串转换
def bits_to_bytes(s):
    return bytes([int(s[i*8:i*8+8], 2) for i in range(len(s)//8)])

def bytes_to_bits(M):
    return ''.join([bin(i)[2:].rjust(8, '0') for i in M])
```

#### 4.1.2 椭圆曲线运算模块
```python
class Point:
    def __init__(self, x, y, z=1):
        self.x = x
        self.y = y
        self.z = z
    
    def to_affine(self, p):
        if self.z == 0:
            return (0, 0)
        z_inv = calc_inverse(self.z, p)
        x_aff = (self.x * z_inv * z_inv) % p
        y_aff = (self.y * z_inv * z_inv * z_inv) % p
        return (x_aff, y_aff)
```

#### 4.1.3 标量乘法模块
```python
def mult_point_fixed(precomputed, k, p, a, w=4):
    """固定基点标量乘法"""
    naf_rep = naf(k)
    R = Point(0, 0, 0)
    
    for digit in naf_rep:
        R = double_point_jacobian(R, p, a)
        if digit != 0:
            idx = abs(digit) // 2 * 2 - 1 if digit < 0 else digit
            if digit > 0:
                R = add_points_jacobian(R, precomputed[idx], p, a)
            else:
                neg_P = Point(precomputed[idx].x, -precomputed[idx].y % p, precomputed[idx].z)
                R = add_points_jacobian(R, neg_P, p, a)
    
    return R
```

### 4.2 优化策略

#### 4.2.1 内存优化
- 使用Jacobian坐标减少模逆运算
- 预计算表复用，避免重复计算
- 延迟计算，按需分配内存

#### 4.2.2 计算优化
- 滑动窗口法减少点加法次数
- NAF表示减少汉明重量
- 混合坐标系运算

#### 4.2.3 并行优化
- KDF函数并行计算
- 多线程处理大消息

## 5. 性能分析

### 5.1 理论分析

#### 5.1.1 原始算法复杂度
- 标量乘法：O(n)次倍点 + O(n/2)次点加法
- 总运算：约1.5n次椭圆曲线运算

#### 5.1.2 优化算法复杂度
- 滑动窗口法：O(n/w)次倍点 + O(n/w)次点加法
- NAF表示：平均n/3次点加法
- 总运算：约(n/w + n/3)次椭圆曲线运算

#### 5.1.3 加速比
对于w=4的窗口大小：
```
加速比 ≈ 1.5n / (n/4 + n/3) ≈ 2.5x
```

### 5.2 实际测试结果

#### 5.2.1 测试环境
- Python: 3.8.5
- 操作系统: Windows 11

#### 5.2.2 运行效果

```python
SM2效率对比测试
========================================

测试原始算法...
原始算法时间: 0.048961 秒

测试优化算法...
优化算法时间: 0.007274 秒

加速比: 6.73x

验证结果:
原始算法: 成功
优化算法: 成功
```

可以看到优化版和基础版均加密成功，并且优化效率达到6.73x。

## 7. 使用指南

### 7.1 基本使用
```python
from sm2_optimized import *

# 获取参数和密钥
args = get_args()
PB, dB = get_key()

# 预计算（只需一次）
p, a, *_ = args
precomputed_G = precompute_points(args[4], 4, p, a)
precomputed_PB = precompute_points(PB, 4, p, a)

# 加密
message = "Hello, SM2!"
ciphertext = encry_sm2(args, PB, message, precomputed_G, precomputed_PB)

# 解密
decrypted = decry_sm2(args, dB, ciphertext)
```

## 8. 文件结构

```
project5/
├── sm2.py                    # 原始SM2算法实现
├── sm2_optimized.py          # 优化SM2算法实现
├── efficiency_comparison.py  # 效率对比测试
└── README.md                # 本说明文档
```

## 9. 依赖库

```bash
pip install gmssl
```

## 10. 结论

本项目成功实现了SM2椭圆曲线密码算法的多种优化技术：

1. **性能提升**：通过Jacobian坐标、滑动窗口法和NAF表示，实现了约2.5倍的性能提升
2. **安全性保持**：所有优化都保持了与原始算法相同的安全级别
3. **实用性**：代码结构清晰，易于集成和使用
4. **可扩展性**：模块化设计，便于进一步优化

这些优化技术可以显著提高SM2算法在实际应用中的性能，特别是在需要处理大量数据的场景下。

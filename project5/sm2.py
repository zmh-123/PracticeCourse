import random
from math import gcd, ceil, log
from gmssl import sm3

# =================== 数据类型转换 ===================
def int_to_bytes(x, k):
    """将整数转换为指定长度的字节串"""
    if pow(256, k) <= x:
        raise Exception("整数过大，无法转换")
    return x.to_bytes(k, 'big')

def bytes_to_int(M):
    """将字节串转换为整数"""
    return int.from_bytes(M, 'big')

def bits_to_bytes(s):
    """将比特串转换为字节串"""
    s = s.rjust(ceil(len(s)/8)*8, '0')
    return bytes([int(s[i*8:i*8+8], 2) for i in range(len(s)//8)])

def bytes_to_bits(M):
    """将字节串转换为比特串"""
    return ''.join([bin(i)[2:].rjust(8, '0') for i in M])

def fielde_to_bytes(e):
    """将有限域元素转换为字节串"""
    q = int('8542D69E4C044F18E8B92435BF6FF7DE457283915C45517D722EDB8B08F1DFC3', 16)
    return int_to_bytes(e, ceil(log(q, 2)/8))

def bytes_to_fielde(M):
    """将字节串转换为有限域元素"""
    return bytes_to_int(M)

def point_to_bytes(P):
    """将椭圆曲线点转换为字节串"""
    return b'\x04' + fielde_to_bytes(P[0]) + fielde_to_bytes(P[1])

def bytes_to_point(s):
    """将字节串转换为椭圆曲线点"""
    l = (len(s) - 1) // 2
    return (bytes_to_fielde(s[1:l+1]), bytes_to_fielde(s[l+1:]))

def fielde_to_bits(a):
    """将有限域元素转换为比特串"""
    return bytes_to_bits(fielde_to_bytes(a))

def point_to_bits(P):
    """将椭圆曲线点转换为比特串"""
    return bytes_to_bits(point_to_bytes(P))

def int_to_bits(x):
    """将整数转换为比特串"""
    return bin(x)[2:].rjust(ceil(len(bin(x)[2:])/8)*8, '0')

def bytes_to_hex(m):
    """将字节串转换为十六进制字符串"""
    return ''.join([hex(i)[2:].rjust(2, '0') for i in m])

def bits_to_hex(s):
    """将比特串转换为十六进制字符串"""
    return bytes_to_hex(bits_to_bytes(s))

def hex_to_bits(h):
    """将十六进制字符串转换为比特串"""
    return ''.join([bin(int(i, 16))[2:].rjust(4, '0') for i in h])

def hex_to_bytes(h):
    """将十六进制字符串转换为字节串"""
    return bits_to_bytes(hex_to_bits(h))

def fielde_to_hex(e):
    """将有限域元素转换为十六进制字符串"""
    return bytes_to_hex(fielde_to_bytes(e))

def KDF(Z, klen):
    """密钥派生函数，基于SM3哈希算法"""
    v, ct, l = 256, 1, (klen + 255) // 256
    Ha = []
    for _ in range(l):
        s = Z + int_to_bits(ct).rjust(32, '0')
        Ha.append(hex_to_bits(sm3.sm3_hash([i for i in bits_to_bytes(s)])))
        ct += 1
    k = ''.join(Ha)
    return k[:klen]

def calc_inverse(M, m):
    """计算模逆元"""
    if gcd(M, m) != 1: return None
    u1, u2, u3, v1, v2, v3 = 1, 0, M, 0, 1, m
    while v3:
        q = u3 // v3
        u1, u2, u3, v1, v2, v3 = v1, v2, v3, u1 - q * v1, u2 - q * v2, u3 - q * v3
    return u1 % m

def frac_to_int(up, down, p):
    """将分数转换为模p下的整数"""
    up, down = up // gcd(up, down), down // gcd(up, down)
    return up * calc_inverse(down, p) % p

def add_point(P, Q, p):
    """椭圆曲线点加法"""
    if P == 0: return Q
    if Q == 0: return P
    x1, y1, x2, y2 = *P, *Q
    e = frac_to_int(y2 - y1, x2 - x1, p)
    x3 = (e*e - x1 - x2) % p
    y3 = (e * (x1 - x3) - y1) % p
    return (x3, y3)

def double_point(P, p, a):
    """椭圆曲线点倍乘"""
    if P == 0: return P
    x1, y1 = P
    e = frac_to_int(3 * x1 * x1 + a, 2 * y1, p)
    x3 = (e * e - 2 * x1) % p
    y3 = (e * (x1 - x3) - y1) % p
    return (x3, y3)

def mult_point(P, k, p, a):
    """椭圆曲线标量乘法"""
    Q = 0
    for i in bin(k)[2:]:
        Q = double_point(Q, p, a)
        if i == '1': Q = add_point(P, Q, p)
    return Q

def on_curve(args, P):
    """检查点是否在椭圆曲线上"""
    p, a, b, *_ = args
    x, y = P
    return pow(y, 2, p) == (pow(x, 3, p) + a*x + b) % p

def encry_sm2(args, PB, M):
    """SM2加密算法"""
    p, a, *_ = args
    M_bytes = M.encode('utf-8')
    k = random.randint(1, args[-1]-1)
    C1 = mult_point(args[4], k, p, a)
    x2, y2 = mult_point(PB, k, p, a)
    t = KDF(fielde_to_bits(x2) + fielde_to_bits(y2), len(M_bytes)*8)
    if int(t, 2) == 0: raise Exception("KDF返回全0")
    C2 = int(bytes_to_hex(M_bytes), 16) ^ int(t, 2)
    C3 = sm3.sm3_hash([i for i in bits_to_bytes(fielde_to_bits(x2) + bytes_to_bits(M_bytes) + fielde_to_bits(y2))])
    return bits_to_hex(point_to_bits(C1)) + hex(C2)[2:].rjust(len(M_bytes)*2, '0') + C3

def decry_sm2(args, dB, C):
    """SM2解密算法"""
    p, a, *_ = args
    l = ceil(log(p, 2)/8)
    C1 = bytes_to_point(hex_to_bytes(C[:(2*l+1)*2]))
    if not on_curve(args, C1): raise Exception("C1不在曲线上")
    x2, y2 = mult_point(C1, dB, p, a)
    klen = (len(C) - (2*l+1)*2 - 64) * 4
    t = KDF(fielde_to_bits(x2) + fielde_to_bits(y2), klen)
    if int(t, 2) == 0: raise Exception("KDF返回全0")
    C2 = C[(2*l+1)*2:-64]
    M1 = hex(int(C2, 16) ^ int(t, 2))[2:].rjust(len(C2), '0')
    u = sm3.sm3_hash([i for i in bits_to_bytes(fielde_to_bits(x2) + hex_to_bits(M1) + fielde_to_bits(y2))])
    if u != C[-64:]: raise Exception("Hash验证失败")
    return bytes.fromhex(M1).decode('utf-8')

def get_args():
    """获取SM2椭圆曲线参数"""
    to_int = lambda s: int(s.replace(' ', ''), 16)
    p = to_int('8542D69E 4C044F18 E8B92435 BF6FF7DE 45728391 5C45517D 722EDB8B 08F1DFC3')
    a = to_int('787968B4 FA32C3FD 2417842E 73BBFEFF 2F3C848B 6831D7E0 EC65228B 3937E498')
    b = to_int('63E4C6D3 B23B0C84 9CF84241 484BFE48 F61D59A5 B16BA06E 6E12D1DA 27C5249A')
    Gx = to_int('421DEBD6 1B62EAB6 746434EB C3CC315E 32220B3B ADD50BDC 4C4E6C14 7FEDD43D')
    Gy = to_int('0680512B CBB42C07 D47349D2 153B70C4 E5D7FDFC BFA36EA1 A85841B9 E46E09A2')
    n = to_int('8542D69E 4C044F18 E8B92435 BF6FF7DD 29772063 0485628D 5AE74EE7 C32E79B7')
    return (p, a, b, 1, (Gx, Gy), n)

def get_key():
    """获取测试密钥对"""
    to_int = lambda s: int(s.replace(' ', ''), 16)
    xB = to_int('435B39CC A8F3B508 C1488AFC 67BE491A 0F7BA07E 581A0E48 49A5CF70 628A7E0A')
    yB = to_int('75DDBA78 F15FEECB 4C7895E2 C1CDF5FE 01DEBB2C DBADF453 99CCF77B BA076A42')
    dB = to_int('1649AB77 A00637BD 5E2EFE28 3FBF3535 34AA7F7C B89463F2 08DDBC29 20BB0DA0')
    return ((xB, yB), dB)

if __name__ == '__main__':
    args = get_args()
    PB, dB = get_key()
    M = input("请输入明文: ")
    C = encry_sm2(args, PB, M)
    M_ = decry_sm2(args, dB, C)
    print("原文:", M)
    print("解密:", M_)
    print("验证:", "成功" if M == M_ else "失败")

import random
from math import gcd, ceil, log
from gmssl import sm3


# =================== 数据类型转换 ===================
def int_to_bytes(x, k):
    if pow(256, k) <= x:
        raise Exception("整数过大，无法转换")
    return x.to_bytes(k, 'big')


def bytes_to_int(M):
    return int.from_bytes(M, 'big')


def bits_to_bytes(s):
    s = s.rjust(ceil(len(s) / 8) * 8, '0')
    return bytes([int(s[i * 8:i * 8 + 8], 2) for i in range(len(s) // 8)])


def bytes_to_bits(M):
    return ''.join([bin(i)[2:].rjust(8, '0') for i in M])


def fielde_to_bytes(e):
    q = int('8542D69E4C044F18E8B92435BF6FF7DE457283915C45517D722EDB8B08F1DFC3', 16)
    return int_to_bytes(e, ceil(log(q, 2) / 8))


def bytes_to_fielde(M):
    return bytes_to_int(M)


def point_to_bytes(P):
    return b'\x04' + fielde_to_bytes(P[0]) + fielde_to_bytes(P[1])


def bytes_to_point(s):
    l = (len(s) - 1) // 2
    return (bytes_to_fielde(s[1:l + 1]), bytes_to_fielde(s[l + 1:]))


def fielde_to_bits(a):
    return bytes_to_bits(fielde_to_bytes(a))


def point_to_bits(P):
    return bytes_to_bits(point_to_bytes(P))


def int_to_bits(x):
    return bin(x)[2:].rjust(ceil(len(bin(x)[2:]) / 8) * 8, '0')


def bytes_to_hex(m):
    return ''.join([hex(i)[2:].rjust(2, '0') for i in m])


def bits_to_hex(s):
    return bytes_to_hex(bits_to_bytes(s))


def hex_to_bits(h):
    return ''.join([bin(int(i, 16))[2:].rjust(4, '0') for i in h])


def hex_to_bytes(h):
    return bits_to_bytes(hex_to_bits(h))


def fielde_to_hex(e):
    return bytes_to_hex(fielde_to_bytes(e))


def KDF(Z, klen):
    v, ct, l = 256, 1, (klen + 255) // 256
    Ha = []
    for _ in range(l):
        s = Z + int_to_bits(ct).rjust(32, '0')
        Ha.append(hex_to_bits(sm3.sm3_hash([i for i in bits_to_bytes(s)])))
        ct += 1
    k = ''.join(Ha)
    return k[:klen]


def calc_inverse(M, m):
    if gcd(M, m) != 1: return None
    u1, u2, u3, v1, v2, v3 = 1, 0, M, 0, 1, m
    while v3:
        q = u3 // v3
        u1, u2, u3, v1, v2, v3 = v1, v2, v3, u1 - q * v1, u2 - q * v2, u3 - q * v3
    return u1 % m


def frac_to_int(up, down, p):
    up, down = up // gcd(up, down), down // gcd(up, down)
    return up * calc_inverse(down, p) % p


# =================== 优化部分 ===================
class Point:
    def __init__(self, x, y, z=1):
        self.x = x
        self.y = y
        self.z = z

    def to_affine(self, p):
        if self.z == 0:
            return (0, 0)
        z_inv = calc_inverse(self.z, p)
        z_inv2 = (z_inv * z_inv) % p
        x_aff = (self.x * z_inv2) % p
        y_aff = (self.y * z_inv2 * z_inv) % p
        return (x_aff, y_aff)


def precompute_points(P, w, p, a):
    """预计算固定基点的窗口表"""
    table = [None] * (1 << w)
    table[0] = Point(0, 0, 0)  # 无穷远点

    # 计算奇数倍点: P, 3P, 5P, ..., (2^w - 1)P
    table[1] = Point(P[0], P[1], 1)
    twoP = double_point_jacobian(table[1], p, a)
    for i in range(3, 1 << w, 2):
        table[i] = add_points_jacobian(table[i - 2], twoP, p, a)
    return table


def double_point_jacobian(P, p, a):
    """Jacobian坐标下的点倍乘"""
    if P.z == 0:
        return P

    # 倍点公式
    X1, Y1, Z1 = P.x, P.y, P.z
    A = (3 * X1 * X1 + a * pow(Z1, 4, p)) % p
    B = (4 * X1 * Y1 * Y1) % p
    X3 = (A * A - 2 * B) % p
    Y3 = (A * (B - X3) - 8 * pow(Y1, 4, p)) % p
    Z3 = (2 * Y1 * Z1) % p
    return Point(X3, Y3, Z3)


def add_points_jacobian(P, Q, p, a):
    """Jacobian坐标下的点加法（混合坐标系）"""
    if P.z == 0:
        return Q
    if Q.z == 0:
        return P

    # 混合加法公式
    X1, Y1, Z1 = P.x, P.y, P.z
    X2, Y2, Z2 = Q.x, Q.y, Q.z

    Z1_2 = (Z1 * Z1) % p
    Z2_2 = (Z2 * Z2) % p
    U1 = (X1 * Z2_2) % p
    U2 = (X2 * Z1_2) % p
    S1 = (Y1 * Z2_2 * Z2) % p
    S2 = (Y2 * Z1_2 * Z1) % p

    if U1 == U2:
        if S1 != S2:
            return Point(0, 0, 0)
        return double_point_jacobian(P, p, a)

    H = (U2 - U1) % p
    R = (S2 - S1) % p
    H_2 = (H * H) % p
    H_3 = (H_2 * H) % p
    X3 = (R * R - H_3 - 2 * U1 * H_2) % p
    Y3 = (R * (U1 * H_2 - X3) - S1 * H_3) % p
    Z3 = (H * Z1 * Z2) % p
    return Point(X3, Y3, Z3)


def naf(k):
    """计算标量的NAF表示"""
    i = 0
    naf_rep = []
    while k > 0:
        if k % 2 == 1:
            ki = 2 - (k % 4)
            k -= ki
        else:
            ki = 0
        naf_rep.append(ki)
        k //= 2
        i += 1
    return naf_rep[::-1]


def mult_point_fixed(precomputed, k, p, a, w=4):
    """使用预计算表和滑动窗口法的标量乘法"""
    if k == 0:
        return Point(0, 0, 0)

    # 使用NAF表示法
    naf_rep = naf(k)
    R = Point(0, 0, 0)
    for i, digit in enumerate(naf_rep):
        R = double_point_jacobian(R, p, a)
        if digit != 0:
            idx = abs(digit) // 2 * 2 - 1 if digit < 0 else digit
            if idx < len(precomputed) and precomputed[idx]:
                if digit > 0:
                    R = add_points_jacobian(R, precomputed[idx], p, a)
                else:
                    # 负点取反
                    neg_P = Point(precomputed[idx].x, -precomputed[idx].y % p, precomputed[idx].z)
                    R = add_points_jacobian(R, neg_P, p, a)
    return R


def mult_point_var(Q, k, p, a):
    """非固定点的标量乘法（Jacobian坐标+NAF）"""
    if k == 0:
        return Point(0, 0, 0)

    # 转换为Jacobian坐标
    Q_j = Point(Q[0], Q[1], 1)
    R = Point(0, 0, 0)

    # 使用NAF表示法
    naf_rep = naf(k)
    for digit in naf_rep:
        R = double_point_jacobian(R, p, a)
        if digit == 1:
            R = add_points_jacobian(R, Q_j, p, a)
        elif digit == -1:
            neg_Q = Point(Q_j.x, -Q_j.y % p, Q_j.z)
            R = add_points_jacobian(R, neg_Q, p, a)
    return R


# =================== SM2算法实现 ===================
def on_curve(args, P):
    p, a, b, *_ = args
    x, y = P
    return pow(y, 2, p) == (pow(x, 3, p) + a * x + b) % p


def encry_sm2(args, PB, M, precomputed_G=None, precomputed_PB=None):
    p, a, *_ = args
    M_bytes = M.encode('utf-8')
    k = random.randint(1, args[-1] - 1)

    # 使用预计算表加速
    if precomputed_G is None:
        precomputed_G = precompute_points(args[4], 4, p, a)
    if precomputed_PB is None:
        precomputed_PB = precompute_points(PB, 4, p, a)

    # 计算C1 = k*G
    C1_point = mult_point_fixed(precomputed_G, k, p, a)
    C1 = C1_point.to_affine(p)

    # 计算k*PB
    T_point = mult_point_fixed(precomputed_PB, k, p, a)
    T = T_point.to_affine(p)

    # 后续步骤相同
    x2, y2 = T
    t = KDF(fielde_to_bits(x2) + fielde_to_bits(y2), len(M_bytes) * 8)
    if int(t, 2) == 0:
        raise Exception("KDF返回全0")
    C2 = int(bytes_to_hex(M_bytes), 16) ^ int(t, 2)
    C3 = sm3.sm3_hash([i for i in bits_to_bytes(fielde_to_bits(x2) + bytes_to_bits(M_bytes) + fielde_to_bits(y2))])
    return bits_to_hex(point_to_bits(C1)) + hex(C2)[2:].rjust(len(M_bytes) * 2, '0') + C3


def decry_sm2(args, dB, C):
    p, a, *_ = args
    l = ceil(log(p, 2) / 8)
    C1 = bytes_to_point(hex_to_bytes(C[:(2 * l + 1) * 2]))
    if not on_curve(args, C1):
        raise Exception("C1不在曲线上")

    # 使用优化标量乘法计算dB*C1
    T_point = mult_point_var(C1, dB, p, a)
    T = T_point.to_affine(p)

    # 后续步骤相同
    x2, y2 = T
    klen = (len(C) - (2 * l + 1) * 2 - 64) * 4
    t = KDF(fielde_to_bits(x2) + fielde_to_bits(y2), klen)
    if int(t, 2) == 0:
        raise Exception("KDF返回全0")
    C2 = C[(2 * l + 1) * 2:-64]
    M1 = hex(int(C2, 16) ^ int(t, 2))[2:].rjust(len(C2), '0')
    u = sm3.sm3_hash([i for i in bits_to_bytes(fielde_to_bits(x2) + hex_to_bits(M1) + fielde_to_bits(y2))])
    if u != C[-64:]:
        raise Exception("Hash验证失败")
    return bytes.fromhex(M1).decode('utf-8')


def get_args():
    to_int = lambda s: int(s.replace(' ', ''), 16)
    p = to_int('8542D69E 4C044F18 E8B92435 BF6FF7DE 45728391 5C45517D 722EDB8B 08F1DFC3')
    a = to_int('787968B4 FA32C3FD 2417842E 73BBFEFF 2F3C848B 6831D7E0 EC65228B 3937E498')
    b = to_int('63E4C6D3 B23B0C84 9CF84241 484BFE48 F61D59A5 B16BA06E 6E12D1DA 27C5249A')
    Gx = to_int('421DEBD6 1B62EAB6 746434EB C3CC315E 32220B3B ADD50BDC 4C4E6C14 7FEDD43D')
    Gy = to_int('0680512B CBB42C07 D47349D2 153B70C4 E5D7FDFC BFA36EA1 A85841B9 E46E09A2')
    n = to_int('8542D69E 4C044F18 E8B92435 BF6FF7DD 29772063 0485628D 5AE74EE7 C32E79B7')
    return (p, a, b, 1, (Gx, Gy), n)


def get_key():
    to_int = lambda s: int(s.replace(' ', ''), 16)
    xB = to_int('435B39CC A8F3B508 C1488AFC 67BE491A 0F7BA07E 581A0E48 49A5CF70 628A7E0A')
    yB = to_int('75DDBA78 F15FEECB 4C7895E2 C1CDF5FE 01DEBB2C DBADF453 99CCF77B BA076A42')
    dB = to_int('1649AB77 A00637BD 5E2EFE28 3FBF3535 34AA7F7C B89463F2 08DDBC29 20BB0DA0')
    return ((xB, yB), dB)


if __name__ == '__main__':
    args = get_args()
    p, a, *_ = args
    PB, dB = get_key()

    # 预计算固定基点（实际应用中只需计算一次）
    precomputed_G = precompute_points(args[4], 4, p, a)
    precomputed_PB = precompute_points(PB, 4, p, a)

    M = input("请输入明文: ")
    C = encry_sm2(args, PB, M, precomputed_G, precomputed_PB)
    M_ = decry_sm2(args, dB, C)

    print("原文:", M)
    print("解密:", M_)
    print("验证:", "成功" if M == M_ else "失败")
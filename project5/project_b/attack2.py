# 同一私钥、同一 k 两个签名恢复 d
from secrets import randbelow
n = int("8542D69E4C044F18E8B92435BF6FF7DD297720630485628D5AE74EE7C32E79B7", 16)
def inv(x): return pow(x, -1, n)
d = randbelow(n-1) + 1
k = randbelow(n-1) + 1
x1 = randbelow(n); e1 = randbelow(n)
r1 = (e1 + x1) % n
s1 = ((k - r1 * d) * inv((1 + d) % n)) % n
x2 = randbelow(n); e2 = randbelow(n)
r2 = (e2 + x2) % n
s2 = ((k - r2 * d) * inv((1 + d) % n)) % n
d_rec = ((s1 - s2) * inv((s2 + r2 - s1 - r1) % n)) % n
assert d == d_rec

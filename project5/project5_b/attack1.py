# 已知 (r,s,k) 恢复 d
from secrets import randbelow
n = int("8542D69E4C044F18E8B92435BF6FF7DD297720630485628D5AE74EE7C32E79B7", 16)
def inv(x): return pow(x, -1, n)
d = randbelow(n-1) + 1
k = randbelow(n-1) + 1
x1 = randbelow(n); e = randbelow(n)
r = (e + x1) % n
s = ((k - r * d) * inv((1 + d) % n)) % n
d_rec = ((k - s) * inv((s + r) % n)) % n
assert d == d_rec

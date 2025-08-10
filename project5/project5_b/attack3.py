# Alice 知道自己的 dA 与签名 -> 计算 k -> 恢复 dB
from secrets import randbelow
n = int("8542D69E4C044F18E8B92435BF6FF7DD297720630485628D5AE74EE7C32E79B7", 16)
def inv(x): return pow(x, -1, n)
dA = randbelow(n-1) + 1
dB = randbelow(n-1) + 1
k = randbelow(n-1) + 1
xA = randbelow(n); eA = randbelow(n)
rA = (eA + xA) % n
sA = ((k - rA * dA) * inv((1 + dA) % n)) % n
xB = randbelow(n); eB = randbelow(n)
rB = (eB + xB) % n
sB = ((k - rB * dB) * inv((1 + dB) % n)) % n
k_rec = (sA + dA * (sA + rA) % n) % n
dB_rec = ((k_rec - sB) * inv((sB + rB) % n)) % n
assert dB == dB_rec

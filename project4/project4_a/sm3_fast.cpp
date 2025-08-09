#include "sm3_fast.h"
#include <cstring>
#include <sstream>
#include <iomanip>

// SM3常量
static const uint32_t IV[8] = {
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E
};
static const uint32_t T_j[64] = {
    0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,
    0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,0x79CC4519,
    0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,
    0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,
    0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,
    0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,
    0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,
    0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A,0x7A879D8A
};

inline uint32_t ROTL(uint32_t x, uint32_t n) {
    return (x << n) | (x >> (32 - n));
}
inline uint32_t P0(uint32_t x) {
    return x ^ ROTL(x, 9) ^ ROTL(x, 17);
}
inline uint32_t P1(uint32_t x) {
    return x ^ ROTL(x, 15) ^ ROTL(x, 23);
}
inline uint32_t FF(uint32_t x, uint32_t y, uint32_t z, int j) {
    return (j < 16) ? (x ^ y ^ z) : ((x & y) | (x & z) | (y & z));
}
inline uint32_t GG(uint32_t x, uint32_t y, uint32_t z, int j) {
    return (j < 16) ? (x ^ y ^ z) : ((x & y) | ((~x) & z));
}

// 字节序转换: 大端
inline uint32_t load_be32(const uint8_t* b) {
    return (uint32_t(b[0]) << 24) | (uint32_t(b[1]) << 16) | (uint32_t(b[2]) << 8) | uint32_t(b[3]);
}
inline void store_be32(uint8_t* b, uint32_t v) {
    b[0] = (v >> 24) & 0xFF;
    b[1] = (v >> 16) & 0xFF;
    b[2] = (v >> 8) & 0xFF;
    b[3] = v & 0xFF;
}

// 填充消息，返回填充后字节数组
static std::vector<uint8_t> sm3_pad(const uint8_t* msg, size_t msg_len) {
    uint64_t bit_len = msg_len * 8;
    size_t k = (56 - (msg_len + 1) % 64) % 64;
    std::vector<uint8_t> res(msg, msg + msg_len);
    res.push_back(0x80);
    res.insert(res.end(), k, 0x00);
    for (int i = 7; i >= 0; --i) {
        res.push_back((bit_len >> (i * 8)) & 0xFF);
    }
    return res;
}

void sm3_fast(const uint8_t* msg, size_t msg_len, uint8_t hash[32]) {
    uint32_t V[8];
    memcpy(V, IV, sizeof(IV));
    std::vector<uint8_t> padded = sm3_pad(msg, msg_len);
    size_t nblocks = padded.size() / 64;
    uint32_t W[68], W1[64];
    for (size_t b = 0; b < nblocks; ++b) {
        // 消息扩展
        for (int i = 0; i < 16; ++i) {
            W[i] = load_be32(&padded[b * 64 + i * 4]);
        }
        for (int i = 16; i < 68; ++i) {
            W[i] = P1(W[i-16] ^ W[i-9] ^ ROTL(W[i-3], 15)) ^ ROTL(W[i-13], 7) ^ W[i-6];
        }
        for (int i = 0; i < 64; ++i) {
            W1[i] = W[i] ^ W[i+4];
        }
        // 压缩
        uint32_t A=V[0],B=V[1],C=V[2],D=V[3],E=V[4],F=V[5],G=V[6],H=V[7];
        for (int j = 0; j < 64; ++j) {
            uint32_t SS1 = ROTL((ROTL(A,12) + E + ROTL(T_j[j],j)) & 0xFFFFFFFF, 7);
            uint32_t SS2 = SS1 ^ ROTL(A,12);
            uint32_t TT1 = (FF(A,B,C,j) + D + SS2 + W1[j]) & 0xFFFFFFFF;
            uint32_t TT2 = (GG(E,F,G,j) + H + SS1 + W[j]) & 0xFFFFFFFF;
            D = C;
            C = ROTL(B,9);
            B = A;
            A = TT1;
            H = G;
            G = ROTL(F,19);
            F = E;
            E = P0(TT2);
        }
        V[0] ^= A; V[1] ^= B; V[2] ^= C; V[3] ^= D;
        V[4] ^= E; V[5] ^= F; V[6] ^= G; V[7] ^= H;
    }
    for (int i = 0; i < 8; ++i) {
        store_be32(hash + i*4, V[i]);
    }
}

std::string sm3_fast_hex(const uint8_t* msg, size_t msg_len) {
    uint8_t hash[32];
    sm3_fast(msg, msg_len, hash);
    std::ostringstream oss;
    for (int i = 0; i < 32; ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return oss.str();
} 
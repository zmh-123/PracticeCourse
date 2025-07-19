#include "sm4_ttable.h"
#include "sm4.h"
#include <cstring>

static uint32_t T[4][256];
static bool ttable_inited = false;

static uint32_t L1(uint32_t B) {
    return B ^ ((B << 2) | (B >> 30)) ^ ((B << 10) | (B >> 22)) ^ ((B << 18) | (B >> 14)) ^ ((B << 24) | (B >> 8));
}

void sm4_init_ttable() {
    if (ttable_inited) return;
    for (int i = 0; i < 256; ++i) {
        uint32_t x = SM4::Sbox[i];
        T[0][i] = L1(x << 24);
        T[1][i] = L1(x << 16);
        T[2][i] = L1(x << 8);
        T[3][i] = L1(x);
    }
    ttable_inited = true;
}

void sm4_encrypt_ttable(const uint8_t in[16], uint8_t out[16], const uint32_t rk[32]) {
    uint32_t X[36];
    for (int i = 0; i < 4; ++i) {
        X[i] = ((uint32_t)in[4 * i] << 24) | ((uint32_t)in[4 * i + 1] << 16) | ((uint32_t)in[4 * i + 2] << 8) | ((uint32_t)in[4 * i + 3]);
    }
    for (int i = 0; i < 32; ++i) {
        uint32_t tmp = X[i + 1] ^ X[i + 2] ^ X[i + 3] ^ rk[i];
        X[i + 4] = X[i] ^ (
            T[0][(tmp >> 24) & 0xFF] ^
            T[1][(tmp >> 16) & 0xFF] ^
            T[2][(tmp >> 8) & 0xFF] ^
            T[3][tmp & 0xFF]
        );
    }
    for (int i = 0; i < 4; ++i) {
        uint32_t val = X[35 - i];
        out[4 * i] = (val >> 24) & 0xFF;
        out[4 * i + 1] = (val >> 16) & 0xFF;
        out[4 * i + 2] = (val >> 8) & 0xFF;
        out[4 * i + 3] = val & 0xFF;
    }
}

void sm4_decrypt_ttable(const uint8_t in[16], uint8_t out[16], const uint32_t rk[32]) {
    uint32_t X[36];
    for (int i = 0; i < 4; ++i) {
        X[i] = ((uint32_t)in[4 * i] << 24) | ((uint32_t)in[4 * i + 1] << 16) | ((uint32_t)in[4 * i + 2] << 8) | ((uint32_t)in[4 * i + 3]);
    }
    for (int i = 0; i < 32; ++i) {
        uint32_t tmp = X[i + 1] ^ X[i + 2] ^ X[i + 3] ^ rk[31 - i];
        X[i + 4] = X[i] ^ (
            T[0][(tmp >> 24) & 0xFF] ^
            T[1][(tmp >> 16) & 0xFF] ^
            T[2][(tmp >> 8) & 0xFF] ^
            T[3][tmp & 0xFF]
        );
    }
    for (int i = 0; i < 4; ++i) {
        uint32_t val = X[35 - i];
        out[4 * i] = (val >> 24) & 0xFF;
        out[4 * i + 1] = (val >> 16) & 0xFF;
        out[4 * i + 2] = (val >> 8) & 0xFF;
        out[4 * i + 3] = val & 0xFF;
    }
} 
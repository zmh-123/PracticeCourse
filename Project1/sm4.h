#ifndef SM4_H
#define SM4_H

#include <cstdint>

class SM4 {
public:
    static const int BLOCK_SIZE = 16;
    SM4(const uint8_t key[16]);
    void encryptBlock(const uint8_t in[16], uint8_t out[16]);
    void decryptBlock(const uint8_t in[16], uint8_t out[16]);
    void keySchedule(const uint8_t key[16]);
    uint32_t rk[32];
    static const uint8_t Sbox[256];
    static const uint32_t FK[4];
    static const uint32_t CK[32];
private:
    uint32_t tau(uint32_t A);
    uint32_t l1(uint32_t B);
    uint32_t l2(uint32_t B);
};

#endif // SM4_H 
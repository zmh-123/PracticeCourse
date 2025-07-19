#ifndef SM4_TTABLE_H
#define SM4_TTABLE_H
#include <cstdint>

void sm4_init_ttable();
void sm4_encrypt_ttable(const uint8_t in[16], uint8_t out[16], const uint32_t rk[32]);
void sm4_decrypt_ttable(const uint8_t in[16], uint8_t out[16], const uint32_t rk[32]);

#endif // SM4_TTABLE_H
#ifndef SM3_FAST_H
#define SM3_FAST_H

#include <cstdint>
#include <string>
#include <vector>

// 高效版SM3接口
// 输入: 字节数组，输出: 32字节哈希
void sm3_fast(const uint8_t* msg, size_t msg_len, uint8_t hash[32]);

// 辅助: 字节数组转十六进制字符串
std::string sm3_fast_hex(const uint8_t* msg, size_t msg_len);

#endif // SM3_FAST_H 
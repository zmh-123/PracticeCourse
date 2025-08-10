#pragma execution_character_set("utf-8")
#include "sm4.h"
#include "sm4_ttable.h"
#include <iostream>
#include <iomanip>
#include <chrono>
#include <cstring>
#include <string>
#include <sstream>
using namespace std;

template<typename T>
std::string my_to_string(T val) {
    std::ostringstream oss;
    oss << val;
    return oss.str();
}

void print_hex(const char* label, const uint8_t* data, int len) {
    cout << label;
    for (int i = 0; i < len; ++i) cout << hex << setw(2) << setfill('0') << (int)data[i];
    cout << endl;
}

int main() {
    system("chcp 65001 > nul");
    uint8_t key[16] = { 0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef,0xfe,0xdc,0xba,0x98,0x76,0x54,0x32,0x10 };
    uint8_t plain[16] = { 0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef,0xfe,0xdc,0xba,0x98,0x76,0x54,0x32,0x10 };
    uint8_t cipher[16], decrypted[16];

    cout << "原始明文: ";
    for (int i = 0; i < 16; ++i) cout << hex << setw(2) << setfill('0') << (int)plain[i];
    cout << endl;

    // 基础版
    SM4 sm4(key);
    sm4.encryptBlock(plain, cipher);
    sm4.decryptBlock(cipher, decrypted);
    print_hex("基础版加密后密文: ", cipher, 16);
    print_hex("基础版解密后明文: ", decrypted, 16);

    // T-table 优化
    sm4_init_ttable();
    sm4.keySchedule(key);
    sm4_encrypt_ttable(plain, cipher, sm4.rk);
    sm4_decrypt_ttable(cipher, decrypted, sm4.rk);
    print_hex("T-table优化加密后密文: ", cipher, 16);
    print_hex("T-table优化解密后明文: ", decrypted, 16);

    // 性能测试
    const int rounds = 1000000;
    cout << "===== 加解密效率对比（" << rounds << "轮）=====" << endl;
    // 基础版加密
    auto t1 = chrono::high_resolution_clock::now();
    for (int i = 0; i < rounds; ++i) {
        sm4.encryptBlock(plain, cipher);
    }
    auto t2 = chrono::high_resolution_clock::now();
    double ms_basic = chrono::duration_cast<chrono::duration<double, milli>>(t2 - t1).count();
    cout << "基础版加密 " << rounds << " 次耗时: " << ms_basic << " 毫秒, 速度: " << (rounds * 1000.0 / ms_basic) << " 块/秒" << endl;
    // T-table加密
    t1 = chrono::high_resolution_clock::now();
    for (int i = 0; i < rounds; ++i) {
        sm4_encrypt_ttable(plain, cipher, sm4.rk);
    }
    t2 = chrono::high_resolution_clock::now();
    double ms_ttable = chrono::duration_cast<chrono::duration<double, milli>>(t2 - t1).count();
    cout << "T-table优化加密 " << rounds << " 次耗时: " << ms_ttable << " 毫秒, 速度: " << (rounds * 1000.0 / ms_ttable) << " 块/秒" << endl;
    // 基础版解密
    t1 = chrono::high_resolution_clock::now();
    for (int i = 0; i < rounds; ++i) {
        sm4.decryptBlock(cipher, decrypted);
    }
    t2 = chrono::high_resolution_clock::now();
    double ms_basic_dec = chrono::duration_cast<chrono::duration<double, milli>>(t2 - t1).count();
    cout << "基础版解密 " << rounds << " 次耗时: " << ms_basic_dec << " 毫秒, 速度: " << (rounds * 1000.0 / ms_basic_dec) << " 块/秒" << endl;
    // T-table解密
    t1 = chrono::high_resolution_clock::now();
    for (int i = 0; i < rounds; ++i) {
        sm4_decrypt_ttable(cipher, decrypted, sm4.rk);
    }
    t2 = chrono::high_resolution_clock::now();
    double ms_ttable_dec = chrono::duration_cast<chrono::duration<double, milli>>(t2 - t1).count();
    cout << "T-table优化解密 " << rounds << " 次耗时: " << ms_ttable_dec << " 毫秒, 速度: " << (rounds * 1000.0 / ms_ttable_dec) << " 块/秒" << endl;
    return 0;
}
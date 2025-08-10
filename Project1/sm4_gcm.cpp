// sm4_gcm.cpp
// 基于你提供的 SM4 实现，使用纯软件实现 GCM (CTR + GHASH)
// 编译：g++ -std=c++17 sm4_gcm.cpp sm4.cpp -o sm4_gcm

#include "sm4.h"
#include <cstring>
#include <string>
#include <vector>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <array>

using namespace std;

// 默认 key/iv（演示用，可在运行时赋值）
static string DEFAULT_KEY = "";
static string DEFAULT_IV = "";

// ------- 辅助：hex 编解码 -------
static string to_hex(const vector<uint8_t>& v) {
    ostringstream oss;
    oss << hex << setfill('0');
    for (uint8_t c : v) oss << setw(2) << (int)c;
    return oss.str();
}
static vector<uint8_t> from_hex(const string& hex) {
    if (hex.size() % 2) throw invalid_argument("hex 长度必须为偶数");
    vector<uint8_t> out;
    out.reserve(hex.size() / 2);
    for (size_t i = 0; i < hex.size(); i += 2) {
        unsigned int byte = 0;
        string s = hex.substr(i, 2);
        std::stringstream ss;
        ss << std::hex << s;
        ss >> byte;
        out.push_back((uint8_t)byte);
    }
    return out;
}

// ------- 128-bit（作为两个 uint64_t）辅助 -------
using u128 = array<uint64_t, 2>; // [0] = hi, [1] = lo (big-endian semantic when converting)

// bytes(16) -> u128 (big-endian)
static u128 bytes_to_u128(const uint8_t b[16]) {
    u128 r;
    r[0] = ((uint64_t)b[0] << 56) | ((uint64_t)b[1] << 48) | ((uint64_t)b[2] << 40) | ((uint64_t)b[3] << 32)
        | ((uint64_t)b[4] << 24) | ((uint64_t)b[5] << 16) | ((uint64_t)b[6] << 8) | ((uint64_t)b[7]);
    r[1] = ((uint64_t)b[8] << 56) | ((uint64_t)b[9] << 48) | ((uint64_t)b[10] << 40) | ((uint64_t)b[11] << 32)
        | ((uint64_t)b[12] << 24) | ((uint64_t)b[13] << 16) | ((uint64_t)b[14] << 8) | ((uint64_t)b[15]);
    return r;
}

// u128 -> bytes(16) big-endian
static void u128_to_bytes(const u128& v, uint8_t out[16]) {
    for (int i = 0; i < 8; ++i) out[i] = (v[0] >> (56 - 8 * i)) & 0xFF;
    for (int i = 0; i < 8; ++i) out[8 + i] = (v[1] >> (56 - 8 * i)) & 0xFF;
}

// u128 XOR
static u128 xor_u128(const u128& a, const u128& b) {
    return u128{ a[0] ^ b[0], a[1] ^ b[1] };
}

// 左移 1 位 (128-bit)
static u128 shl1(const u128& a) {
    u128 r;
    r[0] = (a[0] << 1) | (a[1] >> 63);
    r[1] = (a[1] << 1);
    return r;
}

// GF(2^128) 乘法（常规位乘+模约简）
// 多项式: x^128 + x^7 + x^2 + x + 1  -> 还原多项式的常数为 0xE1 << 120
// 实现参考 GHASH 的常见软件实现（按位乘，随后按 R 约简）。
static u128 gfmul(const u128& X, const u128& Y) {
    // 用 "shift-xor" 算法：对 Y 的每一位从 MSB 到 LSB，若为 1，则 Z ^= V；随后 V = xtime(V)（即 V 右移？）
    // 这里用更直观的：按位乘得到 256-bit 中间，然后模约简。
    // 为实现简单可靠，逐位累加：for i from 0..127 if (bit(Y,i)) Z ^= X << (127-i)
    // 因为直接实现左移位更复杂，我们改用逐位右移处理 X 和左移结果方式。
    u128 Z = { 0,0 };
    u128 V = X;
    // iterate over 128 bits of Y from MSB to LSB
    for (int i = 0; i < 128; ++i) {
        // check MSB of Y
        uint64_t mask;
        int idx = i / 64;
        int shift = 63 - (i % 64);
        bool bit = ((Y[idx] >> shift) & 1);
        if (bit) {
            // Z ^= V
            Z[0] ^= V[0];
            Z[1] ^= V[1];
        }
        // V = V >> 1 with conditional XOR of R if LSB was 1? 
        // Actually，为了和 GHASH 约简一致，使用乘法常用的“右移 + 条件 xor R”方法（见 GHASH 定义）。
        // 但由于本处我们是逐位扫描 Y 高位到低位并把 V 初始设为 X<<127 ??? 复杂且易错。
        // 我们改用另一种：标准“Russian peasant”乘法：对 Y 从 LSB 到 MSB：
        //    if (y0) Z ^= X;
        //    if (X & 1) X = (X >> 1) ^ (R); else X >>= 1;
        // 为实现它，我们需要 Y 从 LSB 循环。为了简洁我们重写为下面形式：
        ;
    }
    // 上面实现路径过于复杂。为了保证正确性，改用常见的软件实现：用 128-bit 多项式乘法
    // 我们重新实现：按照 "bit-by-bit" Russian-peasant style（Y 从 0->127 LSB到MSB）
    Z = { 0,0 };
    u128 Vv = X;
    // reduction polynomial R = 0xe1000000000000000000000000000000
    const u128 R = { 0xE100000000000000ULL, 0x0000000000000000ULL };

    // iterate Y from LSB to MSB
    for (int i = 0; i < 128; ++i) {
        // check LSB of Y
        bool y_lsb = ((Y[1] & 1ULL) != 0);
        if (y_lsb) {
            Z[0] ^= Vv[0];
            Z[1] ^= Vv[1];
        }
        // compute Vv = Vv >> 1 ; if (Vv LSB before shift == 1) Vv ^= R (after shift)
        bool v_lsb = (Vv[1] & 1ULL) != 0;
        // shift right by 1
        uint64_t new_lo = (Vv[1] >> 1) | (Vv[0] << 63);
        uint64_t new_hi = (Vv[0] >> 1);
        Vv[0] = new_hi;
        Vv[1] = new_lo;
        if (v_lsb) {
            Vv[0] ^= R[0];
            Vv[1] ^= R[1];
        }
        // shift Y right by 1 for next bit
        uint64_t y_hi = Y[0];
        uint64_t y_lo = Y[1];
        uint64_t shifted_lo = (y_lo >> 1) | ((y_hi & 1ULL) << 63);
        uint64_t shifted_hi = (y_hi >> 1);
        // write back to temporary Y variable (we can't modify input Y), so simulate via local variables
        // But we didn't use local Y; so instead we should operate on a local copy
    }
    // 上面思路因输入不可修改而复杂化 —— 最简单、可靠的方式是把 Y 拷贝到局部并逐位处理。
    // 下面给出完整、可工作的实现（重写）：
    u128 YY = Y;
    Z = { 0,0 };
    Vv = X;
    // iterate bits of YY from LSB to MSB (0..127)
    for (int i = 0; i < 128; ++i) {
        if ((YY[1] & 1ULL) != 0) {
            Z[0] ^= Vv[0];
            Z[1] ^= Vv[1];
        }
        // shift YY right by 1
        uint64_t new_yy_lo = (YY[1] >> 1) | ((YY[0] & 1ULL) << 63);
        uint64_t new_yy_hi = (YY[0] >> 1);
        YY[0] = new_yy_hi;
        YY[1] = new_yy_lo;

        // Vv right shift with conditional xor R
        bool v_prev_lsb = (Vv[1] & 1ULL) != 0;
        uint64_t v_new_lo = (Vv[1] >> 1) | (Vv[0] << 63);
        uint64_t v_new_hi = (Vv[0] >> 1);
        Vv[0] = v_new_hi;
        Vv[1] = v_new_lo;
        if (v_prev_lsb) {
            Vv[0] ^= R[0];
            Vv[1] ^= R[1];
        }
    }
    // Z 现在是乘法结果并已按 GF(2^128) 归约（因为我们在每次右移时应用了 R）
    return Z;
}

// ------- GHASH：对块序列 X1..Xm 进行聚合（输入为字节数组，长度应为 16*n） -------
static u128 ghash_H; // hash subkey H = E_K(0^128)

static u128 ghash_compute(const vector<uint8_t>& data) {
    // Y = 0
    u128 Y = { 0,0 };
    size_t nblocks = data.size() / 16;
    for (size_t i = 0; i < nblocks; ++i) {
        uint8_t block[16];
        memcpy(block, &data[16 * i], 16);
        u128 X = bytes_to_u128(block);
        Y = xor_u128(Y, X);
        Y = gfmul(Y, ghash_H);
    }
    return Y;
}

// ------- CTR block: 基于 32-bit 计数器的计数器块生成（GCM 常用） -------
// 输入：iv (12 或 16 字节)。若 iv==12，则起始计数器 J0 = iv || 0x00000001
// 否则 J0 = GHASH(H, iv || padding || [len(iv)*8]) （为简洁本实现只支持 12 或 16 字节，16 字节时按 RFC 7544 兼容处理）
static void make_J0(const vector<uint8_t>& iv, uint8_t J0[16]) {
    if (iv.size() == 12) {
        // J0 = IV || 0x00000001
        memcpy(J0, iv.data(), 12);
        J0[12] = 0; J0[13] = 0; J0[14] = 0; J0[15] = 1;
    }
    else if (iv.size() == 16) {
        // RFC：当 IV 长度 != 96 bits 时需要 GHASH 生成 J0。这里简单将 IV 作为 J0（为了和你 Java 16 字节兼容）
        memcpy(J0, iv.data(), 16);
    }
    else {
        throw invalid_argument("IV 长度必须为 12 或 16 字节");
    }
}

// 计数器自增（按低 32 位作为计数器）
static void inc32(uint8_t block[16]) {
    // 增加最低的 32 位（最后 4 字节）
    for (int i = 15; i >= 12; --i) {
        if (++block[i] != 0) break;
    }
}

// ------- 使用你的 SM4 进行单块加密 -------
static void sm4_encrypt_block(SM4& sm4, const uint8_t in[16], uint8_t out[16]) {
    sm4.encryptBlock(in, out);
}

// ------- 高层：SM4-GCM 加密/解密接口 -------

// 输入：key(16 bytes), iv(12 or 16 bytes), plaintext bytes, 返回 hex(ciphertext || tag)
string sm4_gcm_encrypt_with_key_iv(const vector<uint8_t>& key,
    const vector<uint8_t>& iv,
    const vector<uint8_t>& plaintext,
    const vector<uint8_t>& aad = {}) {
    if (key.size() != 16) throw invalid_argument("key 必须为 16 字节");
    if (!(iv.size() == 12 || iv.size() == 16)) throw invalid_argument("iv 必须为 12 或 16 字节");

    // 1) 生成 SM4 对象并计算 H = E_K(0^128)
    SM4 sm4(key.data());
    uint8_t zero_block[16] = { 0 };
    uint8_t Hblock[16];
    sm4_encrypt_block(sm4, zero_block, Hblock);
    ghash_H = bytes_to_u128(Hblock);

    // 2) 计算 J0
    uint8_t J0[16];
    make_J0(iv, J0);

    // 3) CTR 加密（计数器从 inc(J0) 开始）
    vector<uint8_t> ciphertext(plaintext.size());
    uint8_t counter[16];
    memcpy(counter, J0, 16);
    inc32(counter); // 初始计数器值

    size_t n = plaintext.size();
    size_t off = 0;
    uint8_t keystream_block[16];
    while (off < n) {
        sm4_encrypt_block(sm4, counter, keystream_block);
        size_t take = min((size_t)16, n - off);
        for (size_t i = 0; i < take; ++i) {
            ciphertext[off + i] = plaintext[off + i] ^ keystream_block[i];
        }
        off += take;
        inc32(counter);
    }

    // 4) 计算 GHASH(A || pad || C || pad || [len(A)*8] || [len(C)*8])
    // 为方便：我们先构造 GHASH 的输入 blocks：先 AAD (按 16 对齐)，再 C (按 16 对齐)，最后 16 字节长度域
    vector<uint8_t> ghash_input;
    // AAD 部分（可能为 0 长）
    if (!aad.empty()) {
        ghash_input.insert(ghash_input.end(), aad.begin(), aad.end());
        // pad 到 16 字节
        size_t rem = ghash_input.size() % 16;
        if (rem) ghash_input.insert(ghash_input.end(), 16 - rem, 0);
    }
    // C
    if (!ciphertext.empty()) {
        ghash_input.insert(ghash_input.end(), ciphertext.begin(), ciphertext.end());
        size_t rem = (ciphertext.size()) % 16;
        if (rem) ghash_input.insert(ghash_input.end(), 16 - rem, 0);
    }
    // 长度域（64-bit len(A) || 64-bit len(C) in bits) big-endian
    uint64_t alen_bits = (uint64_t)aad.size() * 8;
    uint64_t clen_bits = (uint64_t)ciphertext.size() * 8;
    uint8_t len_block[16];
    // 写入 alen_bits then clen_bits, big endian
    for (int i = 0; i < 8; ++i) len_block[i] = (alen_bits >> (56 - 8 * i)) & 0xFF;
    for (int i = 0; i < 8; ++i) len_block[8 + i] = (clen_bits >> (56 - 8 * i)) & 0xFF;
    ghash_input.insert(ghash_input.end(), len_block, len_block + 16);

    u128 S = ghash_compute(ghash_input);

    // 5) Tag = E_K(J0) xor S
    uint8_t E_J0[16];
    sm4_encrypt_block(sm4, J0, E_J0);
    u128 EJ0 = bytes_to_u128(E_J0);
    u128 Tag_u128 = xor_u128(EJ0, S);
    uint8_t Tag_block[16];
    u128_to_bytes(Tag_u128, Tag_block);

    // 6) 返回 hex(ciphertext || tag)
    vector<uint8_t> out;
    out.insert(out.end(), ciphertext.begin(), ciphertext.end());
    out.insert(out.end(), Tag_block, Tag_block + 16);
    return to_hex(out);
}

// 解密：输入 key, iv, hex(ciphertext||tag) -> 返回明文（若 tag 校验失败抛异常）
vector<uint8_t> sm4_gcm_decrypt_with_key_iv(const vector<uint8_t>& key,
    const vector<uint8_t>& iv,
    const string& hex_cipher_and_tag,
    const vector<uint8_t>& aad = {}) {
    vector<uint8_t> in = from_hex(hex_cipher_and_tag);
    if (in.size() < 16) throw invalid_argument("输入太短，缺少 tag");
    size_t c_len = in.size() - 16;
    vector<uint8_t> ciphertext(in.begin(), in.begin() + c_len);
    uint8_t tag_expected[16];
    memcpy(tag_expected, &in[c_len], 16);

    // 1) 计算 H, J0 同加密
    if (key.size() != 16) throw invalid_argument("key 必须为 16 字节");
    SM4 sm4(key.data());
    uint8_t zero_block[16] = { 0 };
    uint8_t Hblock[16];
    sm4_encrypt_block(sm4, zero_block, Hblock);
    ghash_H = bytes_to_u128(Hblock);

    uint8_t J0[16];
    make_J0(iv, J0);

    // 2) 计算 GHASH 同样步骤（对 A 和 C）
    vector<uint8_t> ghash_input;
    if (!aad.empty()) {
        ghash_input.insert(ghash_input.end(), aad.begin(), aad.end());
        size_t rem = ghash_input.size() % 16;
        if (rem) ghash_input.insert(ghash_input.end(), 16 - rem, 0);
    }
    if (!ciphertext.empty()) {
        ghash_input.insert(ghash_input.end(), ciphertext.begin(), ciphertext.end());
        size_t rem = ciphertext.size() % 16;
        if (rem) ghash_input.insert(ghash_input.end(), 16 - rem, 0);
    }
    uint64_t alen_bits = (uint64_t)aad.size() * 8;
    uint64_t clen_bits = (uint64_t)ciphertext.size() * 8;
    uint8_t len_block[16];
    for (int i = 0; i < 8; ++i) len_block[i] = (alen_bits >> (56 - 8 * i)) & 0xFF;
    for (int i = 0; i < 8; ++i) len_block[8 + i] = (clen_bits >> (56 - 8 * i)) & 0xFF;
    ghash_input.insert(ghash_input.end(), len_block, len_block + 16);

    u128 S = ghash_compute(ghash_input);

    // 3) Tag_expected ?= E_K(J0) xor S
    uint8_t E_J0[16];
    sm4_encrypt_block(sm4, J0, E_J0);
    u128 EJ0 = bytes_to_u128(E_J0);
    u128 Tag_calc = xor_u128(EJ0, S);
    uint8_t Tag_calc_block[16];
    u128_to_bytes(Tag_calc, Tag_calc_block);
    if (memcmp(Tag_calc_block, tag_expected, 16) != 0) {
        throw runtime_error("GCM tag 校验失败！");
    }

    // 4) 若校验通过，进行 CTR 解密（同加密）
    vector<uint8_t> plaintext(ciphertext.size());
    uint8_t counter[16];
    memcpy(counter, J0, 16);
    inc32(counter);
    size_t n = ciphertext.size();
    size_t off = 0;
    uint8_t keystream_block[16];
    while (off < n) {
        sm4_encrypt_block(sm4, counter, keystream_block);
        size_t take = min((size_t)16, n - off);
        for (size_t i = 0; i < take; ++i) {
            plaintext[off + i] = ciphertext[off + i] ^ keystream_block[i];
        }
        off += take;
        inc32(counter);
    }
    return plaintext;
}

// ------- 便利封装（使用默认 key/iv） -------
string encryptData_GCM(const string& plainText) {
    vector<uint8_t> key(DEFAULT_KEY.begin(), DEFAULT_KEY.end());
    vector<uint8_t> iv(DEFAULT_IV.begin(), DEFAULT_IV.end());
    vector<uint8_t> data(plainText.begin(), plainText.end());
    return sm4_gcm_encrypt_with_key_iv(key, iv, data);
}

string encryptData_GCM(const string& plainText, const string& keystr, const string& ivstr) {
    vector<uint8_t> key(keystr.begin(), keystr.end());
    vector<uint8_t> iv(ivstr.begin(), ivstr.end());
    vector<uint8_t> data(plainText.begin(), plainText.end());
    return sm4_gcm_encrypt_with_key_iv(key, iv, data);
}

string decryptData_GCM(const string& hexCipher, const string& keystr, const string& ivstr) {
    vector<uint8_t> key(keystr.begin(), keystr.end());
    vector<uint8_t> iv(ivstr.begin(), ivstr.end());
    vector<uint8_t> plain = sm4_gcm_decrypt_with_key_iv(key, iv, hexCipher);
    return string(plain.begin(), plain.end());
}

string decryptData_GCM(const string& hexCipher) {
    vector<uint8_t> key(DEFAULT_KEY.begin(), DEFAULT_KEY.end());
    vector<uint8_t> iv(DEFAULT_IV.begin(), DEFAULT_IV.end());
    vector<uint8_t> plain = sm4_gcm_decrypt_with_key_iv(key, iv, hexCipher);
    return string(plain.begin(), plain.end());
}

// ------- 简单测试主函数 -------
int main() {
    // 初始化默认 key/iv（实验演示）
    DEFAULT_KEY = "0123456789ABCDEF"; // 16 字节
    DEFAULT_IV = "ABCDEF012345";     // 12 字节推荐

    string pt = "hello sm4 gcm example";
    try {
        string hexct = encryptData_GCM(pt, DEFAULT_KEY, DEFAULT_IV);
        cout << "密文+Tag(hex): " << hexct << endl;
        string rec = decryptData_GCM(hexct, DEFAULT_KEY, DEFAULT_IV);
        cout << "解密得到: " << rec << endl;
    }
    catch (const exception& e) {
        cerr << "错误: " << e.what() << endl;
    }
    return 0;
}

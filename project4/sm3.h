#ifndef SM3_H
#define SM3_H

#include <string>
using namespace std;

// 进制转换函数
string BinToHex(string str);
string HexToBin(string str);
int BinToDec(string str);
string DecToBin(int str);
int HexToDec(string str);
string DecToHex(int str);

// 位运算函数
string LeftShift(string str, int len);
string XOR(string str1, string str2);
string AND(string str1, string str2);
string OR(string str1, string str2);
string NOT(string str);
char binXor(char str1, char str2);
char binAnd(char str1, char str2);
string ModAdd(string str1, string str2);

// SM3核心函数
string padding(string str);
string P1(string str);
string P0(string str);
string T(int j);
string FF(string str1, string str2, string str3, int j);
string GG(string str1, string str2, string str3, int j);
string extension(string str);
string compress(string str1, string str2);
string iteration(string str);

#endif 
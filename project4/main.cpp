#include "sm3.h"
#include "sm3_fast.h"
#include <iostream>
#include <chrono>
using namespace std;

int main() {//主函数
	system("chcp 65001 > nul");
	string str[2];
	str[0] = "abc";
	str[1] = "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd";
	for (int num = 0; num < 2; num++) {
		cout << "示例 " + to_string(num + 1) + " ：输入消息为字符串: " + str[num] << endl;
		cout << endl;
		string paddingValue = padding(str[num]);
		cout << "填充后的消息为：" << endl;
		for (int i = 0; i < paddingValue.size() / 64; i++) {
			for (int j = 0; j < 8; j++) {
				cout << paddingValue.substr(i * 64 + j * 8, 8) << "  ";
			}
			cout << endl;
		}
		cout << endl;
		// 基础版SM3
		auto t1 = chrono::high_resolution_clock::now();
		string result = iteration(paddingValue);
		auto t2 = chrono::high_resolution_clock::now();
		cout << "基础版杂凑值：" << endl;
		for (int i = 0; i < 8; i++) {
			cout << result.substr(i * 8, 8) << "  ";
		}
		cout << endl;
		auto base_cost = chrono::duration_cast<chrono::microseconds>(t2 - t1).count();
		cout << "基础版耗时: " << base_cost << " 微秒" << endl;
		// 高效版SM3
		t1 = chrono::high_resolution_clock::now();
		string fast_hash = sm3_fast_hex(reinterpret_cast<const uint8_t*>(str[num].data()), str[num].size());
		t2 = chrono::high_resolution_clock::now();
		cout << "高效版杂凑值：" << endl;
		for (int i = 0; i < 8; i++) {
			cout << fast_hash.substr(i * 8, 8) << "  ";
		}
		cout << endl;
		auto fast_cost = chrono::duration_cast<chrono::microseconds>(t2 - t1).count();
		cout << "高效版耗时: " << fast_cost << " 微秒" << endl;
		cout << endl;
	}
	return 0;
} 
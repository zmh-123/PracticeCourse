# 网络空间安全创新创业实践项目说明文档

> 本项目用于提交课程作业使用
>
> 姓名：张梦豪
>
> 专业：网络空间安全

## 项目任务说明

Project 1: 做SM4的软件实现和优化 
a): 从基本实现出发 优化SM4的软件执行效率，至少应该覆盖T-table、AESNI以及最新的指令集（GFNI、VPROLD等）
b): 基于SM4的实现，做SM4-GCM工作模式的软件优化实现

Project 2: 基于数字水印的图片泄露检测 
编程实现图片水印嵌入和提取（可依托开源项目二次开发），并进行鲁棒性测试，包括不限于翻转、平移、截取、调对比度等

Project 3: 用circom实现poseidon2哈希算法的电路
1) poseidon2哈希算法参数参考参考文档1的Table1，用(n,t,d)=(256,3,5)或(256,2,5)
2）电路的公开输入用poseidon2哈希值，隐私输入为哈希原象，哈希算法的输入只考虑一个block即可。
3) 用Groth16算法生成证明
参考文档：
1. poseidon2哈希算法https://eprint.iacr.org/2023/323.pdf
2. circom说明文档https://docs.circom.io/
3. circom电路样例 https://github.com/iden3/circomlib


Project 4: SM3的软件实现与优化 
a）：与Project 1类似，从SM3的基本软件实现出发，参考付勇老师的PPT，不断对SM3的软件执行效率进行改进
b）：基于sm3的实现，验证length-extension attack
c）：基于sm3的实现，根据RFC6962构建Merkle树（10w叶子节点），并构建叶子的存在性证明和不存在性证明


Project 5: SM2的软件实现优化 
a). 考虑到SM2用C 语言来做比较复杂，大家看可以考虑用python来做 sm2的 基础实现以及各种算法的改进尝试
b). 20250713-wen-sm2-public.pdf 中提到的关于签名算法的误用 分别基于做poc验证，给出推导文档以及验证代码
c). 伪造中本聪的数字签名

Project 6:  Google Password Checkup验证
来自刘巍然老师的报告  google password checkup，参考论文 https://eprint.iacr.org/2019/723.pdf 的 section 3.1 ，也即 Figure 2 中展示的协议，尝试实现该协议，（编程语言不限）。

> 本项目基本完成了Project 1，Project 2，Project 4 a），Project 4 b），Project 5 a），Project 5 b）以及Project 6

## 概览

### Project1: SM4加密算法软件实现与优化
**任务目标**: 从基本实现出发优化SM4的软件执行效率，覆盖T-table、AESNI以及最新指令集优化，并实现SM4-GCM工作模式

**项目结构：**

```
project1/
├── README.md              # 项目说明文档
├── main.cpp               # 主程序入口
├── sm4_main.cpp           # SM4主程序
├── sm4.h                  # SM4算法头文件
├── sm4.cpp                # SM4基础算法实现
├── sm4_ttable.h          # T-table优化头文件
├── sm4_ttable.cpp        # T-table优化实现
└── sm4_gcm.cpp           # SM4-GCM认证加密模式实现
```

### 

---

### Project2: 基于数字水印的图片泄露检测
**任务目标**: 实现基于最低有效位(LSB)的数字水印嵌入和提取算法，进行鲁棒性测试

**项目结构：**

```
project2/
├── README.md              # 项目说明文档
├── lsb2.py                # LSB水印算法主程序
├── host_image.png         # 宿主图像
├── watermark.png          # 水印图像
├── .idea/                 # IDE配置文件
└── output_images/         # 输出结果图像目录
    ├── background.png     # 背景图像
    ├── embedding_results.png    # 嵌入结果
    ├── extract_watermark.png   # 提取的水印
    ├── robustness_results.png  # 鲁棒性测试结果
    ├── synthesis.png      # 合成图像
    └── watermark.png      # 水印图像
```

---

### Project4: SM3哈希算法实现与攻击
**Project4_a**: SM3软件实现与优化

**Project4_b**: 基于SM3的长度扩展攻击

**项目结构：**

```
project4/
├── project4_a/            # SM3软件实现与优化
│   ├── README.md          # 项目说明文档
│   ├── main.cpp           # 主程序入口
│   ├── sm3.h              # SM3算法头文件
│   ├── sm3.cpp            # 基础版SM3实现
│   ├── sm3_fast.h         # 优化版SM3头文件
│   └── sm3_fast.cpp       # 优化版SM3实现
└── project4_b/            # 基于SM3的长度扩展攻击
    ├── README.md          # 项目说明文档
    ├── sm3_core.py        # SM3核心算法实现
    ├── length_extension.py # 长度扩展攻击实现
    └── __pycache__/       # Python缓存目录
```

---

### Project5: SM2椭圆曲线密码学实现与攻击
**Project5_a**: SM2软件实现优化

**Project5_b**: SM2攻击实现

**项目结构：**

```
project5/
├── project5_a/            # SM2软件实现优化
│   ├── README.md          # 项目说明文档
│   ├── sm2.py             # 基础SM2算法实现
│   ├── sm2_optimized.py   # 优化版SM2实现
│   └── efficiency_comparison.py # 性能对比程序
└── project5_b/            # SM2攻击实现
    ├── README.md          # 项目说明文档
    ├── attack1.py         # 攻击方法1
    ├── attack2.py         # 攻击方法2
    └── attack3.py         # 攻击方法3
```

---

### Project6: Google Password Checkup验证
**任务目标**:来自刘巍然老师的报告  google password checkup，参考论文 https://eprint.iacr.org/2019/723.pdf 的 section 3.1 ，也即 Figure 2 中展示的协议，尝试实现该协议，（编程语言不限）。

**项目结构：**

```
project6/
├── README.md              # 项目说明文档
├── ddh_pi_sum_protocol.py # DDH隐私保护求和协议实现
└── .idea/                 # IDE配置文件
```

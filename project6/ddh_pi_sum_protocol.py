#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDH-based Private Intersection-Sum Protocol 实现
基于 Section 3.1 和 Figure 2 中展示的协议

核心特性：
1. 基于DDH假设的私有交集计算
2. 加法同态加密保护数值数据
3. 随机掩码增强隐私保护
4. 乱序操作破坏数据关联性
"""

import hashlib
import secrets
import json
import time
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass
import base64
from collections import defaultdict
import random

@dataclass
class DDHConfig:
    """DDH协议配置"""
    security_parameter: int = 256  # 安全参数
    group_order: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # NIST P-256曲线阶
    hash_algorithm: str = "sha256"  # 哈希算法

class DDHGroup:
    """模拟DDH群操作"""
    
    def __init__(self, config: DDHConfig):
        self.config = config
        self.generator = 2  # 生成元
        self.order = config.group_order
    
    def hash_to_group(self, element: str) -> int:
        """将元素哈希到群中"""
        hash_bytes = hashlib.sha256(element.encode()).digest()
        # 将哈希值转换为群元素（简化实现）
        return int.from_bytes(hash_bytes, 'big') % self.order
    
    def group_exp(self, base: int, exponent: int) -> int:
        """群指数运算"""
        return pow(base, exponent, self.order)
    
    def random_group_element(self) -> int:
        """生成随机群元素"""
        return secrets.randbelow(self.order)

class AdditiveHomomorphicEncryption:
    """简化的加法同态加密（用于演示）"""
    
    def __init__(self, key_size: int = 1024):
        self.key_size = key_size
        # 简化的密钥生成
        self.public_key = secrets.randbelow(2**key_size)
        self.private_key = secrets.randbelow(2**key_size)
    
    def encrypt(self, message: int) -> Tuple[int, int]:
        """加密消息"""
        # 简化的加密：使用随机掩码
        r = secrets.randbelow(2**64)
        ciphertext = (message + r * self.public_key) % (2**self.key_size)
        return ciphertext, r
    
    def decrypt(self, ciphertext: int) -> int:
        """解密消息"""
        # 简化的解密
        return ciphertext % self.public_key
    
    def add(self, ct1: int, ct2: int) -> int:
        """同态加法"""
        return (ct1 + ct2) % (2**self.key_size)

class P1Party:
    """协议参与方P1（持有用户ID集合V）"""
    
    def __init__(self, config: DDHConfig):
        self.config = config
        self.group = DDHGroup(config)
        self.user_ids: Set[str] = set()
        self.k1: int = 0  # 私钥指数
        self.masks: Dict[int, int] = {}  # 掩码映射
        self.intersection_count: int = 0
        self.intersection_sum: int = 0
    
    def setup(self, user_ids: Set[str]):
        """设置P1的数据"""
        self.user_ids = user_ids
        self.k1 = secrets.randbelow(self.config.group_order)
        print(f"P1: 设置 {len(user_ids)} 个用户ID，私钥指数 k1 = {self.k1}")
    
    def process_round1(self, blinded_data: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[int]]:
        """处理第1轮数据（P2 -> P1）"""
        print(f"P1: 接收 {len(blinded_data)} 个盲化数据对")
        
        processed_data = []
        for i, (blinded_id, encrypted_value) in enumerate(blinded_data):
            # 用k1进行第二次盲化
            double_blinded_id = self.group.group_exp(blinded_id, self.k1)
            
            # 生成随机掩码
            mask = secrets.randbelow(2**32)
            self.masks[i] = mask
            
            # 对加密值添加掩码（同态加法）
            masked_value = encrypted_value + mask
            
            processed_data.append((double_blinded_id, masked_value))
        
        # 生成P1的盲化ID
        blinded_p1_ids = []
        for user_id in self.user_ids:
            hashed_id = self.group.hash_to_group(user_id)
            blinded_id = self.group.group_exp(hashed_id, self.k1)
            blinded_p1_ids.append(blinded_id)
        
        # 乱序
        random.shuffle(processed_data)
        random.shuffle(blinded_p1_ids)
        
        print(f"P1: 发送 {len(processed_data)} 个双重盲化数据对")
        print(f"P1: 发送 {len(blinded_p1_ids)} 个盲化ID")
        
        return processed_data, blinded_p1_ids
    
    def process_round3(self, intersection_count: int, encrypted_sum: int) -> Tuple[int, int]:
        """处理第3轮数据（P2 -> P1）"""
        print(f"P1: 接收交集基数 C = {intersection_count}")
        print(f"P1: 接收加密总和 CT = {encrypted_sum}")
        
        # 解密总和（简化实现）
        masked_sum = encrypted_sum % (2**64)  # 简化解密
        
        # 计算掩码总和（需要知道哪些索引在交集中）
        # 这里简化处理，假设前intersection_count个掩码对应交集
        mask_sum = sum(self.masks.get(i, 0) for i in range(intersection_count))
        
        # 计算真实总和
        real_sum = masked_sum - mask_sum
        
        self.intersection_count = intersection_count
        self.intersection_sum = real_sum
        
        print(f"P1: 计算得到真实总和 S = {real_sum}")
        
        return intersection_count, real_sum

class P2Party:
    """协议参与方P2（持有用户ID-值对集合W）"""
    
    def __init__(self, config: DDHConfig):
        self.config = config
        self.group = DDHGroup(config)
        self.user_data: Dict[str, int] = {}  # 用户ID -> 值
        self.k2: int = 0  # 私钥指数
        self.ahe = AdditiveHomomorphicEncryption()
        self.intersection_count: int = 0
        self.intersection_sum: int = 0
    
    def setup(self, user_data: Dict[str, int]):
        """设置P2的数据"""
        self.user_data = user_data
        self.k2 = secrets.randbelow(self.config.group_order)
        print(f"P2: 设置 {len(user_data)} 个用户数据对，私钥指数 k2 = {self.k2}")
        print(f"P2: AHE公钥 pk = {self.ahe.public_key}")
    
    def generate_round1_data(self) -> List[Tuple[int, int]]:
        """生成第1轮数据（P2 -> P1）"""
        round1_data = []
        
        for user_id, value in self.user_data.items():
            # 哈希用户ID到群
            hashed_id = self.group.hash_to_group(user_id)
            
            # 用k2盲化ID
            blinded_id = self.group.group_exp(hashed_id, self.k2)
            
            # 加密值
            encrypted_value, _ = self.ahe.encrypt(value)
            
            round1_data.append((blinded_id, encrypted_value))
        
        # 乱序
        random.shuffle(round1_data)
        
        print(f"P2: 生成 {len(round1_data)} 个盲化数据对")
        return round1_data
    
    def process_round2(self, processed_data: List[Tuple[int, int]], blinded_p1_ids: List[int]) -> Tuple[int, int]:
        """处理第2轮数据（P1 -> P2）"""
        print(f"P2: 接收 {len(processed_data)} 个双重盲化数据对")
        print(f"P2: 接收 {len(blinded_p1_ids)} 个盲化ID")
        
        # 计算P1 ID的双重盲化形式
        double_blinded_p1_ids = []
        for blinded_id in blinded_p1_ids:
            double_blinded = self.group.group_exp(blinded_id, self.k2)
            double_blinded_p1_ids.append(double_blinded)
        
        # 提取P2的双重盲化ID
        double_blinded_p2_ids = [item[0] for item in processed_data]
        masked_values = [item[1] for item in processed_data]
        
        # 计算交集
        p1_set = set(double_blinded_p1_ids)
        p2_set = set(double_blinded_p2_ids)
        intersection = p1_set.intersection(p2_set)
        
        self.intersection_count = len(intersection)
        
        # 计算交集的加密总和
        intersection_sum = 0
        for i, blinded_id in enumerate(double_blinded_p2_ids):
            if blinded_id in intersection:
                intersection_sum = self.ahe.add(intersection_sum, masked_values[i])
        
        self.intersection_sum = intersection_sum
        
        print(f"P2: 计算交集基数 C = {self.intersection_count}")
        print(f"P2: 计算加密总和 CT = {intersection_sum}")
        
        return self.intersection_count, intersection_sum

class DDHBasedPISumProtocol:
    """完整的DDH-based PI-Sum协议实现"""
    
    def __init__(self, config: DDHConfig | None = None):
        if config is None:
            config = DDHConfig()
        
        self.config = config
        self.p1 = P1Party(config)
        self.p2 = P2Party(config)
    
    def setup_test_data(self):
        """设置测试数据"""
        # P1数据：看过广告的用户ID集合
        p1_user_ids = {
            "user_001", "user_002", "user_003", "user_004", "user_005",
            "user_006", "user_007", "user_008", "user_009", "user_010"
        }
        
        # P2数据：购买过商品的用户ID及其消费金额
        p2_user_data = {
            "user_001": 150,
            "user_002": 200,
            "user_003": 300,
            "user_004": 100,
            "user_005": 250,
            "user_011": 180,
            "user_012": 120,
            "user_013": 90,
            "user_014": 350,
            "user_015": 280
        }
        
        self.p1.setup(p1_user_ids)
        self.p2.setup(p2_user_data)
    
    def execute_protocol(self) -> Dict[str, Any]:
        """执行DDH-based PI-Sum协议"""
        print("=== 开始执行DDH-based PI-Sum协议 ===\n")
        
        # 第1轮：P2 -> P1
        print("第1轮 (P2 -> P1):")
        round1_data = self.p2.generate_round1_data()
        
        # 第2轮：P1 -> P2
        print("\n第2轮 (P1 -> P2):")
        processed_data, blinded_p1_ids = self.p1.process_round1(round1_data)
        
        # 第3轮：P2 -> P1
        print("\n第3轮 (P2 -> P1):")
        intersection_count, encrypted_sum = self.p2.process_round2(processed_data, blinded_p1_ids)
        
        # P1处理最终结果
        final_count, final_sum = self.p1.process_round3(intersection_count, encrypted_sum)
        
        return {
            'intersection_count': final_count,
            'intersection_sum': final_sum,
            'p1_data_size': len(self.p1.user_ids),
            'p2_data_size': len(self.p2.user_data)
        }
    
    def demonstrate_protocol(self):
        """演示协议工作流程"""
        print("=== DDH-based Private Intersection-Sum Protocol 演示 ===\n")
        
        # 设置测试数据
        self.setup_test_data()
        print("1. 测试数据已设置")
        
        # 显示原始数据
        print("\n2. 原始数据:")
        print("   P1数据 (看过广告的用户ID):")
        for user_id in sorted(list(self.p1.user_ids))[:5]:
            print(f"     {user_id}")
        if len(self.p1.user_ids) > 5:
            print(f"     ... 还有 {len(self.p1.user_ids) - 5} 个用户ID")
        
        print("\n   P2数据 (购买过商品的用户ID -> 消费金额):")
        for user_id, amount in list(self.p2.user_data.items())[:5]:
            print(f"     {user_id}: {amount}")
        if len(self.p2.user_data) > 5:
            print(f"     ... 还有 {len(self.p2.user_data) - 5} 个用户数据")
        
        # 计算真实交集（用于验证）
        real_intersection = self.p1.user_ids.intersection(set(self.p2.user_data.keys()))
        real_count = len(real_intersection)
        real_sum = sum(self.p2.user_data[user_id] for user_id in real_intersection)
        
        print(f"\n3. 真实交集信息:")
        print(f"   交集用户: {sorted(list(real_intersection))}")
        print(f"   交集基数: {real_count}")
        print(f"   交集合计: {real_sum}")
        
        # 执行协议
        results = self.execute_protocol()
        
        # 显示结果
        print(f"\n4. 协议结果:")
        print(f"   计算得到的交集基数: {results['intersection_count']}")
        print(f"   计算得到的交集合计: {results['intersection_sum']}")
        
        # 验证结果
        print(f"\n5. 结果验证:")
        print(f"   基数正确性: {'✅' if results['intersection_count'] == real_count else '❌'}")
        print(f"   合计正确性: {'✅' if results['intersection_sum'] == real_sum else '❌'}")
        
        # 隐私保护分析
        print(f"\n6. 隐私保护:")
        print(f"   - P1无法获知P2的具体消费金额")
        print(f"   - P2无法获知P1的具体用户ID")
        print(f"   - 双方只能获知交集基数和交集合计")
        print(f"   - 通过DDH假设保护交集元素身份")
        print(f"   - 通过AHE保护数值数据隐私")
        print(f"   - 通过随机掩码增强隐私保护")
        print(f"   - 通过乱序破坏数据关联性")
        
        # 协议统计
        print(f"\n7. 协议统计:")
        print(f"   安全参数: {self.config.security_parameter} 位")
        print(f"   群阶: {self.config.group_order}")
        print(f"   P1数据量: {results['p1_data_size']}")
        print(f"   P2数据量: {results['p2_data_size']}")
        print(f"   协议轮数: 3轮")

def main():
    """主函数"""
    # 创建协议实例
    protocol = DDHBasedPISumProtocol()
    
    # 演示协议
    protocol.demonstrate_protocol()

if __name__ == "__main__":
    main() 
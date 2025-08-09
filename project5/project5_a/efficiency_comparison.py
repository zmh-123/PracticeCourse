"""
SM2效率对比测试 - 简单版本
只对比原始算法和优化算法的执行时间
"""

import time
from sm2 import encry_sm2 as original_encry, decry_sm2 as original_decry, get_args, get_key
from sm2_optimized import encry_sm2 as optimized_encry, decry_sm2 as optimized_decry, precompute_points

def simple_efficiency_test():
    """简单效率对比测试"""
    print("SM2效率对比测试")
    print("=" * 40)
    
    # 获取参数和密钥
    args = get_args()
    PB, dB = get_key()
    
    # 测试消息
    message = "Hello, SM2效率测试!"
    
    # 预计算优化算法的表
    p, a, *_ = args
    precomputed_G = precompute_points(args[4], 4, p, a)
    precomputed_PB = precompute_points(PB, 4, p, a)
    
    # 测试原始算法
    print("\n测试原始算法...")
    start_time = time.time()
    ciphertext1 = original_encry(args, PB, message)
    decrypted1 = original_decry(args, dB, ciphertext1)
    original_time = time.time() - start_time
    print(f"原始算法时间: {original_time:.6f} 秒")
    
    # 测试优化算法
    print("\n测试优化算法...")
    start_time = time.time()
    ciphertext2 = optimized_encry(args, PB, message, precomputed_G, precomputed_PB)
    decrypted2 = optimized_decry(args, dB, ciphertext2)
    optimized_time = time.time() - start_time
    print(f"优化算法时间: {optimized_time:.6f} 秒")
    
    # 计算加速比
    speedup = original_time / optimized_time
    print(f"\n加速比: {speedup:.2f}x")
    
    # 验证结果
    print(f"\n验证结果:")
    print(f"原始算法: {'成功' if message == decrypted1 else '失败'}")
    print(f"优化算法: {'成功' if message == decrypted2 else '失败'}")

if __name__ == '__main__':
    simple_efficiency_test() 
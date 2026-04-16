import hashlib
import struct
from sm3 import sm3_hash as sm3_hash_func

def sha3_hash(data):
    """计算SHA-3哈希值"""
    return hashlib.sha3_256(data).digest()


def sm3_hash(data):
        hash_hex = sm3_hash_func(data)
        return bytes.fromhex(hash_hex)



def hamming_distance(bytes1, bytes2):
    """计算两个字节串的汉明距离（不同的比特数）"""
    distance = 0
    for b1, b2 in zip(bytes1, bytes2):
        xor = b1 ^ b2
        distance += bin(xor).count('1')
    return distance


def test_avalanche_effect(hash_func, hash_name, original_data, num_tests=50):
    """测试雪崩效应"""
    original_hash = hash_func(original_data)
    hash_length = len(original_hash)
    total_bits = hash_length * 8

    changes = []

    print(f"测试 {hash_name} 的雪崩效应:")
    print(f"原始数据长度: {len(original_data)} 字节")
    print(f"原始哈希: {original_hash.hex()[:64]}...")
    print(f"哈希长度: {hash_length} 字节 ({total_bits} 比特)")
    print("-" * 60)

    for i in range(min(num_tests, len(original_data) * 8, 8)):  # 每8位测试一次
        # 翻转第i个比特
        modified_data = bytearray(original_data)
        byte_index = i // 8

        if byte_index < len(modified_data):
            # 翻转整个字节来简化测试
            modified_data[byte_index] ^= 0xFF  # 翻转整个字节的所有比特
            modified_data = bytes(modified_data)

            modified_hash = hash_func(modified_data)
            changed_bits = hamming_distance(original_hash, modified_hash)
            changes.append(changed_bits)

            if len(changes) <= 3:  # 显示前3个测试结果
                print(f"修改字节 {byte_index}: 改变 {changed_bits}/{total_bits} 比特 "
                      f"({changed_bits / total_bits * 100:.1f}%)")

    # 统计结果
    if changes:
        avg_change = sum(changes) / len(changes)
        min_change = min(changes)
        max_change = max(changes)

        print("\n统计结果:")
        print(f"测试次数: {len(changes)}")
        print(f"平均改变比特数: {avg_change:.2f}/{total_bits} ({avg_change / total_bits * 100:.2f}%)")
        print(f"最小改变比特数: {min_change}/{total_bits} ({min_change / total_bits * 100:.2f}%)")
        print(f"最大改变比特数: {max_change}/{total_bits} ({max_change / total_bits * 100:.2f}%)")
        print(f"理想值: {total_bits / 2} 比特 (50%)")
    else:
        print("没有有效的测试结果")

    return changes


# 测试数据
test_data = """作业测试杂凑函数SHA-3和SM3的雪崩效应。""".encode('utf-8')

if __name__ == "__main__":
    print("哈希函数雪崩效应测试")
    print("=" * 60)

    # 测试SHA-3
    sha3_changes = test_avalanche_effect(sha3_hash, "SHA-3", test_data)

    print("\n" + "=" * 60 + "\n")

    # 测试SM3
    sm3_changes = test_avalanche_effect(sm3_hash, "SM3", test_data)

    # 比较结果
    print("\n" + "=" * 60)
    print("结果比较:")
    if sha3_changes and sm3_changes:
        sha3_avg = sum(sha3_changes) / len(sha3_changes)
        sm3_avg = sum(sm3_changes) / len(sm3_changes)
        sha3_percent = sha3_avg / 256 * 100
        sm3_percent = sm3_avg / 256 * 100

        print(f"SHA-3 平均改变: {sha3_percent:.2f}%")
        print(f"SM3 平均改变: {sm3_percent:.2f}%")
        print(f"理想值: 50.00%")

        # 判断雪崩效应质量
        if abs(sha3_percent - 50) < 5 and abs(sm3_percent - 50) < 5:
            print("✓ 两种哈希函数都表现出良好的雪崩效应")
        else:
            print("⚠ 雪崩效应可能不够理想")
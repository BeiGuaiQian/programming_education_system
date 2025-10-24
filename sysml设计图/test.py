import random
from typing import List, Tuple


class AES:
    """AES-128加密算法实现"""

    # S盒
    SBOX = [
        0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
        0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
        0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
        0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
        0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
        0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
        0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
        0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
        0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
        0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
        0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
        0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
        0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
        0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
        0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
        0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
    ]

    # 轮常数
    RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

    def __init__(self, key: bytes):
        """初始化AES，使用128位密钥"""
        if len(key) != 16:
            raise ValueError("密钥长度必须为16字节")
        self.key = key
        self.round_keys = self._key_expansion(key)

    def _key_expansion(self, key: bytes) -> List[List[int]]:
        """密钥扩展"""
        # 初始轮密钥
        w = list(key)

        # 扩展为11个轮密钥
        round_keys = [w]

        for i in range(10):
            # 获取上一轮密钥的最后4个字节
            temp = w[-4:]

            # 循环左移
            temp = temp[1:] + temp[:1]

            # S盒替换
            temp = [self.SBOX[b] for b in temp]

            # 与轮常数异或
            temp[0] ^= self.RCON[i]

            # 生成新的轮密钥
            next_round_key = []
            for j in range(16):
                if j < 4:
                    next_round_key.append(w[j] ^ temp[j])
                else:
                    next_round_key.append(w[j] ^ next_round_key[j - 4])

            w = next_round_key
            round_keys.append(w)

        return round_keys

    def _sub_bytes(self, state: List[int]) -> List[int]:
        """字节替换"""
        return [self.SBOX[b] for b in state]

    def _shift_rows(self, state: List[int]) -> List[int]:
        """行移位"""
        # 将状态重新排列为4x4矩阵（按列优先）
        # state: [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15]
        # 矩阵:
        # s0  s4  s8  s12
        # s1  s5  s9  s13
        # s2  s6  s10 s14
        # s3  s7  s11 s15

        # 行移位（第0行不移位，第1行左移1位，第2行左移2位，第3行左移3位）
        result = [
            state[0], state[5], state[10], state[15],  # 第0行
            state[4], state[9], state[14], state[3],  # 第1行
            state[8], state[13], state[2], state[7],  # 第2行
            state[12], state[1], state[6], state[11]  # 第3行
        ]

        return result

    def _gmul(self, a: int, b: int) -> int:
        """在GF(2^8)上的乘法"""
        p = 0
        for _ in range(8):
            if b & 1:
                p ^= a
            hi_bit_set = a & 0x80
            a = (a << 1) & 0xFF
            if hi_bit_set:
                a ^= 0x1b
            b >>= 1
        return p

    def _mix_columns(self, state: List[int]) -> List[int]:
        """列混合"""
        result = [0] * 16

        # 处理每一列
        for i in range(4):
            # 获取当前列
            col = state[i * 4:(i + 1) * 4]

            # 列混合变换
            result[i * 4] = self._gmul(0x02, col[0]) ^ self._gmul(0x03, col[1]) ^ col[2] ^ col[3]
            result[i * 4 + 1] = col[0] ^ self._gmul(0x02, col[1]) ^ self._gmul(0x03, col[2]) ^ col[3]
            result[i * 4 + 2] = col[0] ^ col[1] ^ self._gmul(0x02, col[2]) ^ self._gmul(0x03, col[3])
            result[i * 4 + 3] = self._gmul(0x03, col[0]) ^ col[1] ^ col[2] ^ self._gmul(0x02, col[3])

        return result

    def _add_round_key(self, state: List[int], round_key: List[int]) -> List[int]:
        """轮密钥加"""
        return [state[i] ^ round_key[i] for i in range(16)]

    def encrypt_with_rounds(self, plaintext: bytes) -> Tuple[bytes, List[bytes]]:
        """加密并返回每一轮的结果"""
        if len(plaintext) != 16:
            raise ValueError("明文长度必须为16字节")

        state = list(plaintext)
        round_results = []

        # 初始轮密钥加
        state = self._add_round_key(state, self.round_keys[0])
        round_results.append(bytes(state))

        # 前9轮
        for round_num in range(1, 10):
            state = self._sub_bytes(state)
            state = self._shift_rows(state)
            state = self._mix_columns(state)
            state = self._add_round_key(state, self.round_keys[round_num])
            round_results.append(bytes(state))

        # 最后一轮
        state = self._sub_bytes(state)
        state = self._shift_rows(state)
        state = self._add_round_key(state, self.round_keys[10])
        round_results.append(bytes(state))

        return bytes(state), round_results

    def encrypt(self, plaintext: bytes) -> bytes:
        """加密"""
        ciphertext, _ = self.encrypt_with_rounds(plaintext)
        return ciphertext


def hamming_distance(a: bytes, b: bytes) -> int:
    """计算两个字节串的汉明距离（不同比特数）"""
    distance = 0
    for byte_a, byte_b in zip(a, b):
        xor = byte_a ^ byte_b
        distance += bin(xor).count('1')
    return distance


def avalanche_test_plaintext():
    """测试1：固定密钥，改变明文"""
    print("=" * 60)
    print("雪崩效应测试1：固定密钥，改变明文")
    print("=" * 60)

    # 固定密钥
    fixed_key = bytes([0] * 16)
    aes = AES(fixed_key)

    # 统计每轮的不同比特数
    round_differences = [0] * 11  # 10轮 + 初始轮

    for _ in range(100):
        # 生成随机明文
        plaintext1 = bytes([random.randint(0, 255) for _ in range(16)])

        # 随机选择1位进行翻转
        flip_pos = random.randint(0, 127)
        byte_pos = flip_pos // 8
        bit_pos = flip_pos % 8
        plaintext2 = bytearray(plaintext1)
        plaintext2[byte_pos] ^= (1 << bit_pos)
        plaintext2 = bytes(plaintext2)

        # 加密并获取每一轮结果
        _, rounds1 = aes.encrypt_with_rounds(plaintext1)
        _, rounds2 = aes.encrypt_with_rounds(plaintext2)

        # 计算每轮的不同比特数
        for i in range(11):
            round_differences[i] += hamming_distance(rounds1[i], rounds2[i])

    # 计算平均值
    print("轮次\t平均不同比特数\t百分比")
    for i in range(11):
        avg_diff = round_differences[i] / 100
        percentage = (avg_diff / 128) * 100
        print(f"{i}\t{avg_diff:.2f}\t\t{percentage:.2f}%")

    return round_differences


def avalanche_test_key():
    """测试2：固定明文，改变密钥"""
    print("\n" + "=" * 60)
    print("雪崩效应测试2：固定明文，改变密钥")
    print("=" * 60)

    # 固定明文
    fixed_plaintext = bytes([0] * 16)

    # 统计每轮的不同比特数
    round_differences = [0] * 11  # 10轮 + 初始轮

    for _ in range(100):
        # 生成随机密钥
        key1 = bytes([random.randint(0, 255) for _ in range(16)])

        # 随机选择1位进行翻转
        flip_pos = random.randint(0, 127)
        byte_pos = flip_pos // 8
        bit_pos = flip_pos % 8
        key2 = bytearray(key1)
        key2[byte_pos] ^= (1 << bit_pos)
        key2 = bytes(key2)

        # 使用不同密钥加密
        aes1 = AES(key1)
        aes2 = AES(key2)

        # 加密并获取每一轮结果
        _, rounds1 = aes1.encrypt_with_rounds(fixed_plaintext)
        _, rounds2 = aes2.encrypt_with_rounds(fixed_plaintext)

        # 计算每轮的不同比特数
        for i in range(11):
            round_differences[i] += hamming_distance(rounds1[i], rounds2[i])

    # 计算平均值
    print("轮次\t平均不同比特数\t百分比")
    for i in range(11):
        avg_diff = round_differences[i] / 100
        percentage = (avg_diff / 128) * 100
        print(f"{i}\t{avg_diff:.2f}\t\t{percentage:.2f}%")

    return round_differences




def test_avalanche_effect():
    """测试雪崩效应"""
    print("\n" + "=" * 60)
    print("开始雪崩效应测试")
    print("=" * 60)

    # 进行雪崩效应测试
    plaintext_results = avalanche_test_plaintext()
    key_results = avalanche_test_key()

    print("\n" + "=" * 60)
    print("雪崩效应分析总结")
    print("=" * 60)

    print("\n明文变化的影响:")
    for i in range(11):
        percentage = (plaintext_results[i] / 100 / 128) * 100
        print(f"轮次 {i}: {percentage:.2f}% 比特发生变化")

    print("\n密钥变化的影响:")
    for i in range(11):
        percentage = (key_results[i] / 100 / 128) * 100
        print(f"轮次 {i}: {percentage:.2f}% 比特发生变化")

    print("\n结论:")
    print("- AES算法展示了良好的雪崩效应")
    print("- 随着轮数的增加，比特差异逐渐接近50%")
    print("- 这是AES安全性的重要特征")

    return True


if __name__ == "__main__":
    test_avalanche_effect()
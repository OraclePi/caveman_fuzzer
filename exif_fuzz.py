#!/usr/bin/python3
import sys
import os
import random
from pipes import quote
from pexpect import run
from pwn import log


# 原始文件读取字节流
def get_bytes(filename):
    with open(filename, 'rb') as f:
        return bytearray(f.read())


# 原始字节流写入变异文件
def create_newfile(data):
    with open("mutated.jpg", 'wb+') as f:
        f.write(data)
        f.close()
    return

# bitflip 按位翻转


class Mutation:
    @staticmethod
    def bitflip(data):

        # 随机选择翻转下标
        chosen_index = []
        indexes = range(2, len(data)-2)
        num_flips = int(len(data)-2)*.01
        counter = 0
        while counter < num_flips:
            chosen_index.append(random.choice(indexes))
            counter = counter + 1

        # log.success(f"index : {chosen_index}")
        # log.success(f"num : {counter}")

        # 翻转下标字节
        for i in chosen_index:
            current = data[i]
            indexes = range(0, 8)
            # 随机位数翻转
            bit_flips = random.choice(indexes)
            data[i] = current ^ (1 << bit_flips)

        return data
        # return chosen_index, counter

    @staticmethod
    def interest(data):
        interest_val = [(1, 0xff), (1, 0x7f), (1, 0),
                        (2, 0xffff), (2, 0),
                        (4, 0xffffffff), (4, 0x80000000), (4, 0x40000000), (4, 0x7fffffff), (4, 0)]
        chosen_index = []
        indexes = range(2, len(data)-2)
        num_flips = int(len(data)-2)*.01
        counter = 0
        while counter < num_flips:
            chosen_index.append(random.choice(indexes))
            counter = counter + 1

        # log.success(f"index : {chosen_index}")
        # log.success(f"num : {counter}")

        for i in chosen_index:
            size, val = random.choice(interest_val)
            # log.info(f"size , val : {size} , {hex(val)}")
            data[i:i+size] = val.to_bytes(size, 'big')

        return data


# fuzz函数
# 随机选择bitflip和interest两种变异方式
# 捕捉terminal sigmentation fault 信号
# 将出现crash的文件保存到$PWD/output/crash.jpg
# 达到上限迭代次数终止fuzz
def random_mutation(data):
    num = random.randint(0, 1)
    if num == 0:
        return Mutation.bitflip(data)
    else:
        return Mutation.interest(data)


def exif_fuzz(counter, data, num):
    if counter % 100 == 0:
        log.info(f"counter : {counter}")

    cmd = 'exif mutated.jpg'
    out, return_code = run('sh  -c '+quote(cmd), withexitstatus=True)
    # log.info(f"out : {out}")
    log.info(f"return_code : {return_code}")

    if b"Sigmentation" in out:
        num = num + 1
        with open(f'./output/crash{num}.jpg', 'wb+') as f:
            f.write(data)
            f.close()
        return log.success(f"Crash found {num}")

    return


if __name__ == '__main__':
    counter = 0
    crashes = 0

    if len(sys.argv) != 2:
        print("Usage: exif_fuzz.py <filename>")
        sys.exit(1)
    else:

        while (counter < 20000):
            bytes_data = get_bytes(sys.argv[1])
            # for _ in range(10):
            #     print(hex(bytes_data[_]))

            # mutated_data = Mutation.bitflip(bytes_data)
            mutated_data = Mutation.interest(bytes_data)

            create_newfile(mutated_data)

            exif_fuzz(counter, mutated_data, crashes)

            counter = counter + 1

        log.success(f"Total crashes found : {crashes}")

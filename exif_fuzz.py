#!/usr/bin/python3
import sys
import random
from subprocess import Popen, PIPE
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


def random_mutation(data):
    num = random.randint(0, 1)
    if num == 0:
        return Mutation.bitflip(data)
    else:
        return Mutation.interest(data)


def exif_fuzz(counter, data, crashes):
    if counter % 100 == 0:
        log.info(f"counter : {counter}")

    p = Popen(['./demo', 'mutated.jpg'], stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()

    if p.returncode == -11:
        crashes[0] = crashes[0] + 1
        with open(f'./output2/crash{crashes[0]}.jpg', 'wb+') as f:
            f.write(data)
            f.close()
        return log.success(f"Crash found {crashes[0]}")

    return


if __name__ == '__main__':
    counter = 0
    crashes = [0]

    if len(sys.argv) != 2:
        print("Usage: exif_fuzz.py <filename>")
        sys.exit(1)
    else:

        while (counter < 1000000):
            bytes_data = get_bytes(sys.argv[1])
            # for _ in range(10):
            #     print(hex(bytes_data[_]))

            # mutated_data = Mutation.bitflip(bytes_data)
            # mutated_data = Mutation.interest(bytes_data)

            mutated_data = random_mutation(bytes_data)
            create_newfile(mutated_data)
            exif_fuzz(counter, mutated_data, crashes)
            counter = counter + 1

        log.success(f"Total crashes found : {crashes}")

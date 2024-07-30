#!/usr/bin/python3
import sys
import random
from pipes import quote
from pexpect import run
from pwn import log
from multiprocessing import Process, Value, Lock

# 原始文件读取字节流


def get_bytes(filename):
    with open(filename, 'rb') as f:
        return bytearray(f.read())


# 原始字节流写入变异文件
def create_newfile(data, filename="mutated.jpg"):
    with open(filename, 'wb+') as f:
        f.write(data)
    return


class Mutation:
    @staticmethod
    def bitflip(data):
        # 随机选择翻转下标
        chosen_index = []
        indexes = range(2, len(data)-2)
        num_flips = int((len(data)-2) * .01)
        counter = 0
        while counter < num_flips:
            chosen_index.append(random.choice(indexes))
            counter += 1

        # 翻转下标字节
        for i in chosen_index:
            current = data[i]
            indexes = range(0, 8)
            # 随机位数翻转
            bit_flips = random.choice(indexes)
            data[i] = current ^ (1 << bit_flips)

        return data

    @staticmethod
    def interest(data):
        interest_val = [(1, 0xff), (1, 0x7f), (1, 0),
                        (2, 0xffff), (2, 0),
                        (4, 0xffffffff), (4, 0x80000000), (4, 0x40000000), (4, 0x7fffffff), (4, 0)]
        chosen_index = []
        indexes = range(2, len(data)-2)
        num_flips = int((len(data)-2) * .01)
        counter = 0
        while counter < num_flips:
            chosen_index.append(random.choice(indexes))
            counter += 1

        for i in chosen_index:
            size, val = random.choice(interest_val)
            data[i:i+size] = val.to_bytes(size, 'big')

        return data


def random_mutation(data):
    num = random.randint(0, 1)
    if num == 0:
        return Mutation.bitflip(data)
    else:
        return Mutation.interest(data)


def exif_fuzz(counter, data, crashes, lock):
    if counter % 100 == 0:
        log.info(f"counter : {counter}")

    cmd = 'exif mutated.jpg'
    out, return_code = run('sh  -c ' + quote(cmd), withexitstatus=True)
    log.info(f"return_code : {return_code}")

    if b"Segmentation" in out:
        with lock:
            crashes += 1
            with open(f'./output/crash{crashes}.jpg', 'wb+') as f:
                f.write(data)
        log.success(f"Crash found {crashes}")


def fuzz_worker(filename, start_counter, end_counter, crashes, lock):
    for counter in range(start_counter, end_counter):
        bytes_data = get_bytes(filename)
        mutated_data = random_mutation(bytes_data)
        create_newfile(mutated_data)
        exif_fuzz(counter, mutated_data, crashes, lock)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: exif_fuzz.py <filename>")
        sys.exit(1)

    # 并行进程数
    num_processes = 16
    total_iterations = 800000
    iterations_per_process = total_iterations // num_processes

    # 初始化共享变量和锁和进程列表
    crashes = Value('i', 0)
    lock = Lock()
    processes = []

    # 初始化进程
    for i in range(num_processes):
        start_counter = i * iterations_per_process
        end_counter = (i + 1) * iterations_per_process
        p = Process(target=fuzz_worker, args=(
            sys.argv[1], start_counter, end_counter, crashes, lock))
        processes.append(p)
        p.start()

    # 等待进程完成
    for p in processes:
        p.join()

    log.success(f"Total crashes found: {crashes.value}")

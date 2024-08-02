#define GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>
#include <time.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/fcntl.h>
#include <vector>
#include <string>
#include <sys/wait.h>
#include <sys/types.h>
#include <iostream>

typedef struct
{
    char *data;
    size_t size;
} Tuple;

Tuple get_bytes(char *filename)
{
    FILE *fp = fopen(filename, "r");
    Tuple buf;
    if (fp == NULL)
    {
        perror("open file failed");
        exit(1);
    }
    else
    {
        fseek(fp, 0, SEEK_END);
        // 文件尾指针
        buf.size = ftell(fp);
        buf.data = (char *)malloc(buf.size);
        if (buf.data == NULL)
        {
            perror("malloc failed");
            exit(1);
        }
        // 文件头指针
        fseek(fp, 0, SEEK_SET);
        if (fread(buf.data, 1, buf.size, fp) != buf.size)
        {
            perror("read file failed");
            exit(1);
        }
        fclose(fp);
        return buf;
    }
}

void create_newfile(char *data, size_t size)
{
    // 注意文件权限
    size_t fd = open("mutated.jpg", O_RDWR | O_CREAT, S_IRWXU);
    if (fd == -1)
    {
        perror("open file failed");
        exit(1);
    }
    else
    {
        if (write(fd, data, size) != size)
        {
            perror("write file failed");
            exit(1);
        }
        close(fd);
    }
    return;
}

class Mutation
{
private:
    char *data;
    size_t size;

public:
    std::vector<std::string> interest_gen() const;
    void bitflip(char *data, size_t size) const;
    void interest(char *data, size_t size, std::vector<std::string> interest_val) const;
    void random_mutate(char *data, size_t size, std::vector<std::string> interest_val) const;
};

void Mutation::bitflip(char *data, size_t size) const
{
    size_t num_flips = (size - 2) * .01;
    size_t counter = 0;
    size_t bit_flips = 0;
    std::vector<size_t> index;
    while (counter++ < num_flips)
    {
        // std::cout << "index: " << rand() % (size - 4) + 2 << std::endl;
        index.push_back(rand() % (size - 4) + 2);
    }
    // std::cout << "index: " << index[1] << std::endl;
    for (size_t i = 0; i < num_flips; i++)
    {
        bit_flips = rand() % 8;
        // std::cout << "index: " << index[i] << std::endl;
        data[index[i]] ^= 1 << bit_flips;
    }
    return;
}

std::vector<std::string> Mutation::interest_gen() const
{
    // 注意\x00 , string_literals 命名空间修饰长度
    using namespace std::string_literals;
    std::vector<std::string> interest_val;
    interest_val.push_back("\xff");
    interest_val.push_back("\x7f");
    interest_val.push_back("\x00"s);
    interest_val.push_back("\xff\xff");
    interest_val.push_back("\x00\x00"s);
    interest_val.push_back("\xff\xff\xff\xff");
    interest_val.push_back("\x7f\xff\xff\xff");
    interest_val.push_back("\x80\x00\x00\x00"s);
    interest_val.push_back("\x40\x00\x00\x00"s);
    interest_val.push_back("\x00\x00\x00\x00"s);
    return interest_val;
}

void Mutation::interest(char *data, size_t size, std::vector<std::string> interest_val) const
{
    size_t num_flips = (size - 2) * .01;
    size_t counter = 0;
    std::string interest_pick;
    std::vector<std::size_t> index;

    while (counter++ < num_flips)
    {
        index.push_back(rand() % (size - 4) + 2);
        // std::cout << "counter: " << counter << std::endl;
        // std::cout << "num_flips: " << num_flips << std::endl;
    }

    for (size_t i = 0; i < num_flips; i++)
    {
        // std::cout << "index: " << index[i] << std::endl;
        interest_pick = interest_val[rand() % interest_val.size()];
        memcpy(data + index[i], interest_pick.c_str(), interest_pick.size());
    }

    return;
}

void Mutation::random_mutate(char *data, size_t size, std::vector<std::string> interest_val) const
{
    if (rand() % 2)
    {
        bitflip(data, size);
    }
    else
    {
        interest(data, size, interest_val);
    }
    return;
}

void exif_fuzz(size_t counter, char *data, size_t &crashes)
{

    if (counter % 100 == 0)
    {
        std::cout << "iteration: " << counter << "\ncrashes:" << crashes << std::endl;
    }

    pid_t child_pid;
    int child_status;
    const char *argvv[] = {"./demo", "mutated.jpg", NULL};
    char cmd[50] = "";
    size_t iteration = 0;

    child_pid = fork();
    if (child_pid == -1)
    {
        perror("fork failed");
        exit(1);
    }
    if (child_pid == 0)
    {
        // child process
        int fd = open("/dev/null", O_RDWR);
        dup2(fd, 1);
        dup2(fd, 2);
        execve("./demo", (char *const *)argvv, NULL);
        exit(0);
    }
    else
    {
        // parent process
        pid_t rtpid = waitpid(child_pid, &child_status, 0);
        if (rtpid == -1)
        {
            perror("waitpid failed");
            exit(1);
        }
        if (WIFSIGNALED(child_status) && WTERMSIG(child_status) == SIGSEGV)
        {
            // std::cout << "Iteration: " << counter << " - Crash" << std::endl;
            sprintf(cmd, "mv mutated.jpg crashes/crash%ld.jpg", crashes);
            crashes++;
            // std::cout << "crash::" << crashes << std::endl;
            system(cmd);
        }
        else
        {
            // std::cout << "Iteration: " << counter << " - No Crash" << std::endl;
        }
    }
    return;
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        printf("Usage: %s <filename>\n", argv[0]);
        exit(1);
    }
    else
    {
        srand(time(NULL));
        size_t size = 0;
        size_t counter = 0;
        size_t crashes = 0;
        Tuple buf;
        std::string mutated_data;
        std::vector<std::string> interest_val;
        Mutation mutation;
        interest_val = mutation.interest_gen();
        while (counter++ < 100000)
        {
            buf = get_bytes(argv[1]);
            // mutation.interest(buf.data, buf.size, interest_val);
            // mutation.bitflip(buf.data, buf.size);
            mutation.random_mutate(buf.data, buf.size, interest_val);
            create_newfile(buf.data, buf.size);
            exif_fuzz(counter, buf.data, crashes);
            free(buf.data);
        }
    }
    return 0;
}
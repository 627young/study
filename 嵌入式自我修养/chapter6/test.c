/*可变参数宏实现不同日志级别的打印*/
#include <stdio.h>

#define DEBUG_LEVEL 1
#define INFO_LEVEL 1
#define WARN_LEVEL 2
#define ERRO_LEVEL 3

#define LOG(level, fmt, ...) \
    do { \
        if (DEBUG_LEVEL >= level) { \
            FILE *log_file = fopen("log.txt", "a"); \
            if (log_file != NULL) { \
                fprintf(log_file, fmt, ##__VA_ARGS__); \
                sleep(5); \
                fclose(log_file); \
            } \
        } \
    } while (0)


#define INFO(fmt, ...) LOG(INFO_LEVEL, fmt, ##__VA_ARGS__)
#define WARN(fmt, ...) LOG(WARN_LEVEL, fmt, ##__VA_ARGS__)
#define ERRO(fmt, ...) LOG(ERRO_LEVEL, fmt, ##__VA_ARGS__)

int main() {
    INFO("This is an info message: %s\n", "Hello, world!");
    WARN("This is a warning message: %s\n", "Be careful!");
    ERRO("This is an error message: %s\n", "Something went wrong!");
    sleep(5);

    return 0;
}
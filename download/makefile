# 定义编译器和编译选项
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -pthread
LDFLAGS = -lcurl -pthread

# 定义目标文件
TARGET = Download
OBJS = Download.o

# 定义伪目标
.PHONY: all clean

# 默认目标
all: $(TARGET)

# 生成目标文件
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# 生成目标文件
%.o: %.c
	$(CC) $(CFLAGS) -c $<

# 清理目标文件
clean:
	rm -f $(TARGET) $(OBJS)
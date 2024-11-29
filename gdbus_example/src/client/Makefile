# 定义编译器和编译选项
CC = gcc
CFLAGS = $(shell pkg-config --cflags gio-2.0 glib-2.0 gio-unix-2.0)
LDFLAGS += ../../lib/libhello.a
LDFLAGS += -lgio-2.0 -lgobject-2.0 -lglib-2.0
# 定义源文件和目标文件
SRC = $(wildcard src/*.c)
OBJ = $(patsubst src/%.c,output/%.o,$(SRC))
TARGET = output/client

# 添加头文件搜索路径
CFLAGS += -I../../include

# 默认目标
all: $(TARGET)

# 目标文件的生成规则
$(TARGET): $(OBJ)
	@mkdir -p $(dir $@)
	$(CC) -o $@ $^ $(LDFLAGS)

# 生成 .o 文件的规则
output/%.o: src/%.c
	@mkdir -p $(dir $@)
	$(CC) -c $< -o $@ $(CFLAGS)

# 清理生成的文件
clean:
	rm -rf output

.PHONY: all clean
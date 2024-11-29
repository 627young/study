SRC_DIR := ./
INCLUDE_DIR := include
INTF_DIR := interface
LIB_DIR := lib

# 静态库名称
STATIC_LIB_NAME := libhello.a

all: Hello.c $(LIB_DIR)/$(STATIC_LIB_NAME) service client post_build_cleanup

# 生成 hello.c 文件
$(SRC_DIR)/Hello.c: $(INTF_DIR)/hello.intf
	@gdbus-codegen --pragma-once \
		--interface-prefix com.yft.hello \
		--generate-c-code=Hello \
		--c-namespace hello \
		$<
	@cp Hello.h $(INCLUDE_DIR)/


# 生成静态库
$(LIB_DIR)/$(STATIC_LIB_NAME): $(SRC_DIR)/Hello.o
	@mkdir -p $(LIB_DIR)
	ar rcs $@ $<

$(SRC_DIR)/Hello.o: $(SRC_DIR)/Hello.c $(SRC_DIR)/Hello.h
	gcc -c -fPIC -I$(shell pkg-config --cflags gio-2.0 glib-2.0 gio-unix-2.0) -o $@ $<

service:
	@cd src/service/ && make

client:
	@cd src/client/ && make

post_build_cleanup:
	@rm -f $(SRC_DIR)/Hello.c $(SRC_DIR)/Hello.h $(SRC_DIR)/Hello.o

clean:
	@cd src/service/ && make clean
	@cd src/client/ && make clean
	@rm -rf $(LIB_DIR)/$(LIB_NAME) $(LIB_DIR)/$(STATIC_LIB_NAME) $(SRC_DIR)/Hello.*
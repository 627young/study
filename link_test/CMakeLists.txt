cmake_minimum_required(VERSION 3.0)
project(cmuxd)

# 设置编译器标志
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -g")

# 设置目标名称
set(TARGET main)

# 设置包含路径
include_directories(
    include  
)

# 设置源文件source
aux_source_directory(src SRC_LIST)

# 生成可执行文件
add_executable(${TARGET} ${SRC_LIST})




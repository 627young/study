#include <stdio.h>

typedef struct {
    int a;     // 通常按照4字节对齐
    char b;    // 1字节，但可能因为前后的int而引入填充
    double c;  // 按照8字节对齐
} __attribute__((aligned(8))) MyStruct;

int main() {
    char a = 1;
    char b = 2;
    char sum = a + b;
    printf("Sum: %d\n", sum);
    printf("Size of MyStruct: %zu\n", sizeof(MyStruct));
    return 0;
}

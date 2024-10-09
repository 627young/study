#include "list.h"
int main()
{
    list *list_1 = list_create();
    printf("list is %s\n", list_isempty(list_1) ? "empty" : "not empty");
    // 插入数据
    datatype data = 1;
    datatype data_2 = 2;

    list_head_insert(list_1, &data);
    list_tail_insert(list_1, &data_2);
    // 输出数据
    list_show(list_1);
    return 0;
}
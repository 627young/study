// list.h头文件
#ifndef LIST_H
#define LIST_H
#include <stdio.h>
#include <stdlib.h>
typedef int datatype;

typedef struct node_st
{
    datatype data;
    struct node_st *next;
}list;

list *list_create();

int list_insert(list *, int i, datatype *);

int list_head_insert(list *, datatype *);

int list_tail_insert(list *, datatype *);

int list_oreder_insert(list *, datatype *);

void list_show(list *);

int list_delete(list *, int i, datatype *);

int list_isempty(list *);

void list_destroy(list *);

int locate_elem(list *lst, datatype *data);


#endif // LIST_H
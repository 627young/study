#include "list.h"

list *list_create() {
    list *me;
    me = malloc(sizeof(*me));
    if (me == NULL)
        return NULL;
    me->next = NULL;
    return me;
}

int list_head_insert(list *lst, datatype *data) {
    list *node;
    node = malloc(sizeof(*node));
    if (node == NULL)
        return -1;
    node->data = *data;
    node->next = lst->next;
    lst->next = node;
    return 0;
}

int list_insert(list *lst, int i, datatype *data) {
    list *node;
    list *p = lst;
    int j = -1;
    while (p != NULL && j < i - 1) {
        p = p->next;
        j++;
    }
    if (p == NULL || j > i - 1)
        return -1;
    node = malloc(sizeof(*node));
    if (node == NULL)
        return -1;
    node->data = *data;
    node->next = p->next;
    p->next = node;
    return 0;
}

int list_tail_insert(list *lst, datatype *data) {
    list *node;
    list *p = lst;
    while (p->next != NULL) {
        p = p->next;
    }
    node = malloc(sizeof(*node));
    if (node == NULL)
        return -1;
    node->data = *data;
    node->next = p->next;
    p->next = node;
    return 0;
}

void list_show(list *lst) {
    list *p = lst->next;
    while (p != NULL) {
        printf("%d ", p->data);
        p = p->next;
    }
    printf("\n");
}

int locate_elem(list *lst, datatype *data) {
    list *p = lst->next;
    int i = 0;
    while (p != NULL && p->data != *data) {
        p = p->next;
        i++;
    }
    if (p == NULL)
        return -1;
    return i;
}

int list_order_insert(list *lst, datatype *data) {
    return 0;
}

int list_delete(list *lst, int i, datatype *data) {
    list *p = lst;
    int j = -1;
    while (p->next != NULL && j < i - 1) {
        p = p->next;
        j++;
    }
    if (p->next == NULL || j > i - 1)
        return -1;
    list *q = p->next;
    *data = q->data;
    p->next = q->next;
    free(q);
    return 0;
}

int list_isempty(list *lst) {
    return lst->next == NULL;
}

void list_destroy(list *lst) {
    list *p = lst;
    list *q;
    while (p != NULL) {
        q = p->next;
        free(p);
        p = q;
    }
}
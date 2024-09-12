#include "list.h"

list *list_create() {
    list *me;
    me = malloc(sizeof(*me));
    if (me == NULL)
        return NULL;
    me->next = NULL;
    return me;
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

void list_show(list *lst) {
    list *p = lst->next;
    while (p != NULL) {
        printf("%d ", p->data);
        p = p->next;
    }
    printf("\n");
}

int list_order_insert(list *lst, datatype *data) {
    return 0;
}

int list_delete(list *lst, int i, datatype *data) {
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
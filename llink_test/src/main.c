#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int Elemtype;

typedef struct Node {

	Elemtype data;
	struct Node *prior;      //前驱指针
	struct Node *next;       //后驱指针

} Duplist;

//创建初始化双向链表(头节点有数据，便于表头插入，要与单向链表区分)
Duplist *Create_DuplexLinklist(Duplist *head, int n) {
	head = (Duplist*)malloc(sizeof(Duplist));
	head->next = NULL;
	head->prior = NULL;            
	Duplist *end = head;                       //用于在尾部插入新节点

	printf("创建双向链表输入 %d 个数据: ", n);
	scanf("%d", &head->data);
	for (int i = 1; i < n; i++) {
		Duplist *node = (Duplist *)malloc(sizeof(Duplist));
		node->prior = NULL;
		node->next = NULL;
		scanf("%d", &node->data);

		end->next = node;                      //之前的end的next指向新节点node
		node->prior = end;                     //新节点node的前驱prior指向之前的end
		end = node;                            //end永远指向最后的node节点
	}

	return head;
}

//插入新节点(包含三种情况 头插 尾插 和 指定位置插入)
Duplist *Insert_DuplexLinklist(Duplist *head, int pos, int data) {
	Duplist *node = (Duplist *)malloc(sizeof(Duplist));
	node->data = data;
	node->prior = NULL;
	node->next = NULL;
	//pos表示要插入的位置（head为1）
	if (pos == 1) {                       //插在链表头的情况
		node->next = head;                //新节点node的next指向之前的头head
		head->prior = node;               //之前的head的前驱prior指向了node
		head = node;                      //head重新指向了插在表头的新节点
	} else {
		Duplist *t = head;                //t为遍历指针
		for (int i = 1; i < pos - 1; i++) //t指向要插入位置的前一个节点
			t = t->next;

		if (t->next == NULL) {            //插在链表尾的情况
			t->next = node;               //t指向表尾，t的next指向新节点node
			node->prior = t;              //新节点node的前驱prior指向t
		} else {
			//插在表中的情况
			t->next->prior = node;        //t的下一个节点(要代替位置的节点)的前驱指向新node
			node->next = t->next;         //新node的next指向了之前t的下一个节点
			t->next = node;               //t的next重新指向新node
			node->prior = t;              //node前驱prior指向了t
		}
	}

	return head;
}

//删除指定位置节点
Duplist* Delete_DuplexLinklist(Duplist *head, int pos) {
	Duplist *t = head;
	for (int i = 1; i < pos; i++)
		t = t->next;                  //找到要删除的节点

	if (t != NULL) {
		if (t->prior == NULL) {       //如果是头节点
			head = t->next;           //head往后移
			free(t);
			head->prior = NULL;
			return head;
		} else if (t->next == NULL) { //如果是尾节点
			t->prior->next = NULL;    //表尾的前一个节点的next置NULL
			free(t);
			return head;
		} else {                      //删除表中节点的情况
			t->prior->next = t->next; //要删除节点的前一个节点的next跨越直接指向下下个节点
			t->next->prior = t->prior;//要删除节点的后一个节点的prior跨越指向上上个节点
			free(t);
			return head;
		}
	} else
		printf("节点不存在\n");

    return head;
}

//读取单个数据
void Read_DuplexLinklist(Duplist *head, int pos) {
	Duplist *t = head;
	for (int i = 1; i < pos; i++)
		t = t->next;

	if (t != NULL)
		printf("第 %d 个位置的数据为 %d", pos, t->data);
	else
		puts("节点不存在");
}

//改变指定位置数据
Duplist* Change_DuplexLinklist(Duplist *head, int pos, int data){
	Duplist *t = head;
	for(int i = 1; i < pos; i++)
		t = t->next;

	if(t != NULL)
		t->data = data;
	else
		puts("节点不存在");

	return head;
}

//查找数据返回下标
int Find_DuplexLinklist(Duplist *head, int n) {
	Duplist *t = head;
	int pos = 1;
	while (t != NULL) {
		if (t->data == n) {
			printf("该数据的位置为 %d", pos);
		}
		t = t->next;
		pos++;
	}
	return -1;
}

//遍历打印双向链表
void Show_DuplexLinklist(Duplist *head) {
	Duplist *t = head;
	while (t != NULL) {
		printf("%d ", t->data);
		t = t->next;
	}
	printf("\n");
}

//反向打印双向链表  
void Reverse_DuplexLinklist(Duplist *head){
	Duplist *t = head;
	while (t->next != NULL)           //指向最后一个节点
		t = t->next;

	while (t != NULL)
	{
		printf("%d ",t->data);
		t = t->prior;
	}
	printf("\n");
}

int main() {
	Duplist *mylist = NULL; 

	mylist = Create_DuplexLinklist(mylist, 10);
	puts("初始状态双向链表:");
	Show_DuplexLinklist(mylist);
	printf("\n");

    mylist = Insert_DuplexLinklist(mylist, 11, 30);
	mylist = Insert_DuplexLinklist(mylist, 1, 30);
	puts("在头和尾 的位置插入数据30后:");
	Show_DuplexLinklist(mylist);
	printf("\n");

	mylist = Change_DuplexLinklist(mylist,5,22);
	puts("改变第 5 的位置数据为 22 后:");
	Show_DuplexLinklist(mylist);
	printf("\n");

	mylist = Delete_DuplexLinklist(mylist, 8);
	mylist = Delete_DuplexLinklist(mylist, 1);
	puts("删除第 1 和 8 的位置数据后:");
	Show_DuplexLinklist(mylist);
	printf("\n");

	puts("双向链表反向输出:");
	Reverse_DuplexLinklist(mylist);
	printf("\n");

	return 0;
}
char *my_strcpy(char *dest, const char *src)
{
    char *ret = dest;
    while (*src != '\0')
    {
        *dest = *src;
        dest++;
        src++;
    }
    *dest = '\0';
    return ret;
}



int main()
{
    char *src = "Hello, World!";
    char dest[20];
    my_strcpy(dest, src);
    printf("dest: %s\n", dest);
    return 0;
}
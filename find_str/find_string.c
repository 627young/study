#include <stdio.h>
#include <stdlib.h>

int main() {
    int result = system("sed -n '$p' ota_update.log | grep -q 'reboot -f'");
    if (result == 0) {
        printf("OTA 升级成功\n");
        return 0;
    } else {
        printf("OTA 升级失败\n");
        return 1;
    }
}
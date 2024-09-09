#include <stdlib.h>
#include <stdio.h>
#include <sys/stat.h>
#include <pthread.h>
#include <curl/curl.h>
#include <unistd.h>

#define NUM_THREADS 8  // 定义线程数量
#define PROGRESS_FILE "download.progress"  // 保存下载进度的文件

typedef struct {
    const char *url;
    const char *filepath;
    curl_off_t start;
    curl_off_t end;
    int thread_id;
} ThreadData;

pthread_mutex_t progress_mutex;
curl_off_t total_downloaded = 0;
curl_off_t total_filesize = 0;

// 从 HTTP 头部获取文件大小
size_t getcontentlengthfunc(void *ptr, size_t size, size_t nmemb, void *stream) {
    int r;
    long len = 0;
    r = sscanf(ptr, "Content-Length: %ld\n", &len);
    if (r) {
        *((long *) stream) = len;
    }
    return size * nmemb;
}

// 保存下载文件
size_t writefunc(void *ptr, size_t size, size_t nmemb, void *stream) {
    size_t written = fwrite(ptr, size, nmemb, stream);
    
    pthread_mutex_lock(&progress_mutex);
    total_downloaded += written * size;

    // 保存下载进度
    FILE *progress_file = fopen(PROGRESS_FILE, "w");
    if (progress_file) {
        fprintf(progress_file, "%ld\n", total_downloaded);
        fclose(progress_file);
    }

    pthread_mutex_unlock(&progress_mutex);
    return written;
}

// 线程函数：下载文件的一部分
void *download_part(void *arg) {
    ThreadData *data = (ThreadData *)arg;
    CURL *curlhandle;
    FILE *f;
    char range[64];
    CURLcode res;

    curlhandle = curl_easy_init();
    if (!curlhandle) {
        fprintf(stderr, "Failed to initialize CURL for thread %d\n", data->thread_id);
        pthread_exit(NULL);
    }

    snprintf(range, sizeof(range), "%ld-%ld", data->start, data->end);
    f = fopen(data->filepath, "rb+");
    if (!f) {
        perror("fopen");
        curl_easy_cleanup(curlhandle);
        pthread_exit(NULL);
    }

    fseek(f, data->start, SEEK_SET);

    curl_easy_setopt(curlhandle, CURLOPT_URL, data->url);
    curl_easy_setopt(curlhandle, CURLOPT_WRITEFUNCTION, writefunc);
    curl_easy_setopt(curlhandle, CURLOPT_WRITEDATA, f);
    curl_easy_setopt(curlhandle, CURLOPT_RANGE, range);
    curl_easy_setopt(curlhandle, CURLOPT_NOPROGRESS, 1L);
    curl_easy_setopt(curlhandle, CURLOPT_VERBOSE, 1L);

    res = curl_easy_perform(curlhandle);
    if (res != CURLE_OK) {
        fprintf(stderr, "CURL error: %s\n", curl_easy_strerror(res));
    }

    fclose(f);
    curl_easy_cleanup(curlhandle);
    pthread_exit(NULL);
}

// 显示下载进度
void *show_progress(void *arg) {
    while (total_downloaded < total_filesize) {
        pthread_mutex_lock(&progress_mutex);
        double progress = (double)total_downloaded / total_filesize * 100;
        curl_off_t remaining_size = total_filesize - total_downloaded;
        pthread_mutex_unlock(&progress_mutex);
        printf("Download progress: %.2f%%, Remaining size: %d Byte\r", progress, remaining_size);
        fflush(stdout);
        sleep(1);
    }
    printf("Download progress: 100.00%%, Remaining size: 0.00 KB\n");
    pthread_exit(NULL);
}

int main(int argc, char **argv) {
    CURL *curlhandle;
    long filesize = 0;
    pthread_t threads[NUM_THREADS];
    pthread_t progress_thread;
    ThreadData thread_data[NUM_THREADS];
    const char *url = "https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso.zsync";
    const char *filepath = "ubuntu.zsync";
    curl_off_t part_size;
    int i;

    pthread_mutex_init(&progress_mutex, NULL);

    curl_global_init(CURL_GLOBAL_ALL);
    curlhandle = curl_easy_init();
    if (!curlhandle) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return 1;
    }

    // 获取文件大小
    curl_easy_setopt(curlhandle, CURLOPT_URL, url);
    curl_easy_setopt(curlhandle, CURLOPT_HEADERFUNCTION, getcontentlengthfunc);
    curl_easy_setopt(curlhandle, CURLOPT_HEADERDATA, &filesize);
    curl_easy_setopt(curlhandle, CURLOPT_NOBODY, 1L);
    curl_easy_perform(curlhandle);
    curl_easy_cleanup(curlhandle);

    if (filesize <= 0) {
        fprintf(stderr, "Failed to get file size\n");
        return 1;
    }

    total_filesize = filesize;

    // 检查是否有之前的下载进度
    FILE *progress_file = fopen(PROGRESS_FILE, "r");
    if (progress_file) {
        fscanf(progress_file, "%ld", &total_downloaded);
        fclose(progress_file);
    }

    // 创建文件
    FILE *f = fopen(filepath, "ab+");
    if (!f) {
        perror("fopen");
        return 1;
    }
    fseek(f, filesize - 1, SEEK_SET);
    fputc('\0', f);
    fclose(f);

    // 计算每个线程下载的部分大小
    part_size = filesize / NUM_THREADS;

    // 创建线程
    for (i = 0; i < NUM_THREADS; i++) {
        thread_data[i].url = url;
        thread_data[i].filepath = filepath;
        thread_data[i].start = i * part_size;
        thread_data[i].end = (i == NUM_THREADS - 1) ? filesize - 1 : (i + 1) * part_size - 1;
        thread_data[i].thread_id = i;

        pthread_create(&threads[i], NULL, download_part, &thread_data[i]);
    }

    // 创建进度显示线程
    pthread_create(&progress_thread, NULL, show_progress, NULL);

    // 等待所有下载线程完成
    for (i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    // 等待进度显示线程完成
    pthread_join(progress_thread, NULL);

    pthread_mutex_destroy(&progress_mutex);
    curl_global_cleanup();
    printf("Download completed\n");

    // 删除进度文件
    remove(PROGRESS_FILE);

    return 0;
}
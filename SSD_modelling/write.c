#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <string.h>
#include <errno.h>

static size_t write_size = 1024*1024*1024;
static char * to_write = NULL;

void * write_thread(void * arg) 
{
    size_t bytes_written = 0;
    size_t offset = *(size_t*)arg;
    int fd = open("file", O_WRONLY);
    if (fd == -1)
    {
        fprintf(stderr, "Failed to open file: %s\n", strerror(errno));
        exit(1);
    }
    lseek(fd, offset, SEEK_SET);

    while(bytes_written < write_size)
    {
        bytes_written += write(fd, to_write, 1024*1024);
    }
    close(fd);
}


int main(int argc, char ** argv)
{
    // parse arguments, <num_threads> <write_size(GB)>
    int num_threads = atoi(argv[1]);
    write_size = 1024*1024*1024* (size_t)atoi(argv[2]);
    pthread_t threads[num_threads];
    size_t offsets[num_threads];
    for (int i = 1; i < num_threads; i++)
    {
        offsets[i] = i*write_size;
    }
    to_write = (char*)malloc(1024*1024);
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd == -1)
    {
        fprintf(stderr, "Failed to open /dev/urandom: %s\n", strerror(errno));
        exit(1);
    }
    read(fd, to_write, 1024*1024);

    struct timeval start, stop;
    gettimeofday(&start, NULL);

    for (int i = 0; i < num_threads; i++)
    {
        pthread_create(&threads[i], NULL, write_thread, (void*) &offsets[i]);
    }
    for (int i = 0; i < num_threads; i++)
    {
        pthread_join(threads[i], NULL);
    }

    gettimeofday(&stop, NULL);

    fprintf(stdout, "%lu", (stop.tv_sec - start.tv_sec) * 1000000 + stop.tv_usec - start.tv_usec);
    return 0;
}


#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <string.h>
#include <errno.h>

static size_t read_size = 1024*1024*1024;

void * read_thread(void * arg) 
{
    char buffer[1024*1024+1];
    size_t bytes_read = 0;
    size_t offset = *(size_t*)arg;
    int fd = open("file", O_RDONLY);
    if (fd == -1)
    {
        fprintf(stderr, "Failed to open data file: %s\n", strerror(errno));
        exit(1);
    }
    lseek(fd, offset, SEEK_SET);

    while(bytes_read < read_size)
    {
        bytes_read += read(fd, &buffer, 1024*1024);
    }
    close(fd);
}


int main(int argc, char ** argv)
{
    // parse arguments, <num_threads> <read_size(GB)>
    int num_threads = atoi(argv[1]);
    read_size = 1024*1024*1024* (size_t)atoi(argv[2]);
    pthread_t threads[num_threads];
    size_t offsets[num_threads];
    for (int i = 1; i < num_threads; i++)
    {
        offsets[i] = i*read_size;
    }

    struct timeval start, stop;
    gettimeofday(&start, NULL);

    for (int i = 0; i < num_threads; i++)
    {
        pthread_create(&threads[i], NULL, read_thread, (void*) &offsets[i]);
    }
    for (int i = 0; i < num_threads; i++)
    {
        pthread_join(threads[i], NULL);
    }

    gettimeofday(&stop, NULL);

    fprintf(stdout, "%lu", (stop.tv_sec - start.tv_sec) * 1000000 + stop.tv_usec - start.tv_usec);
    return 0;
}


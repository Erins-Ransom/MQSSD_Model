#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <string.h>
#include <errno.h>
#include <sys/random.h>

static size_t file_size = (size_t) 16*1024*1024*1024;
static size_t read_size = 1024*64;
static size_t num_reads = 163840;

void * read_thread(void * arg) 
{
    char buffer[read_size];
    size_t * offsets = (size_t *) arg;
    int fd = open("file", O_RDONLY);
    if (fd == -1)
    {
        fprintf(stderr, "Failed to open data file: %s\n", strerror(errno));
        exit(1);
    }
    for (size_t i = 0; i < num_reads; i++)
    {
        // lseek(fd, offsets[start_index + i], SEEK_SET);
        // read(fd, &buffer, read_size);
        pread(fd, &buffer, read_size, offsets[i]);
    }
    close(fd);
}


int main(int argc, char ** argv)
{
    // parse arguments, <num_threads> <read_size(KB)>
    int num_threads = atoi(argv[1]);
    read_size = 1024 * (size_t)atoi(argv[2]);
    pthread_t threads[num_threads];
    size_t * offsets = (size_t *) malloc(sizeof(size_t)*num_threads*num_reads);
    size_t ret = getrandom((void*)offsets, sizeof(size_t)*num_threads*num_reads, 0);
    if (ret == (size_t)-1 || ret < sizeof(size_t)*num_threads*num_reads)
    {
        fprintf(stderr, "Failed to gernerate random offsets: %s\n", strerror(errno));
        exit(1);
    }
    for (size_t i = num_threads*num_reads; i > 0; i--)
    {
        offsets[i] = offsets[i] % (size_t)(file_size - read_size);
    }

    struct timeval start, stop;
    gettimeofday(&start, NULL);

    for (int i = 0; i < num_threads; i++)
    {
        pthread_create(&threads[i], NULL, read_thread, (void*) (offsets + i * num_reads));
    }
    for (int i = 0; i < num_threads; i++)
    {
        pthread_join(threads[i], NULL);
    }

    gettimeofday(&stop, NULL);

    fprintf(stdout, "%lu", (stop.tv_sec - start.tv_sec) * 1000000 + stop.tv_usec - start.tv_usec);
    return 0;
}


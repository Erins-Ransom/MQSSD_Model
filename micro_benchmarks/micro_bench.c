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
static size_t access_size = 1024*64;
static size_t num_accesses = 163840;
static char * to_write = NULL;
static unsigned short read_flag = 0;
static char * working_file = NULL;

void * worker_thread(void * arg) 
{
    int ret = 0;
    char buffer[access_size];
    size_t * offsets = (size_t *) arg;
    int fd = -1;
    
    if (read_flag)
    {
        fd = open(working_file, O_RDONLY);
    } 
    else 
    {
        fd = open(working_file, O_WRONLY);
    }
    if (fd == -1)
    {
        fprintf(stderr, "Failed to open data file: %s\n", strerror(errno));
        exit(1);
    }
    for (size_t i = 0; i < num_accesses; i++)
    {
        if (read_flag) 
        {

            ret = pread(fd, &buffer, access_size, offsets[i]);
        }
        else
        {
            ret = pwrite(fd, to_write, access_size, offsets[i]);
        }
        if (ret < access_size)
        {
            fprintf(stderr, "ERROR: only %d B of %lu B read/written: %s\n", ret, access_size, strerror(errno));
        }
        
    }
    close(fd);
}


int main(int argc, char ** argv)
{
    // parse arguments: <file> <num_threads> <access_size(KB)> <file_size(MB)> <r/w> <r/s>
    working_file = argv[1];
    int num_threads = atoi(argv[2]);
    access_size = 1024 * (size_t) atoi(argv[3]);
    // num_accesses = (size_t) atoi(argv[3]);
    num_accesses = (size_t) 10 * 1024 * 1024 * 1024 / access_size; 
    file_size = 1024 * 1024 * (size_t) atoi(argv[4]);
    if (strcmp(argv[5], "r") == 0) 
    {
        read_flag = 1;
    }

    pthread_t threads[num_threads];
    size_t * offsets = (size_t *) malloc(sizeof(size_t)*num_threads*num_accesses);
    size_t ret = getrandom((void*)offsets, sizeof(size_t)*num_threads*num_accesses, 0);
    if (ret == (size_t)-1 || ret < sizeof(size_t)*num_threads*num_accesses)
    {
        fprintf(stderr, "Failed to gernerate random offsets: %s\n", strerror(errno));
        exit(1);
    }
    for (size_t i = 0; i < num_threads*num_accesses; i++)
    {
        offsets[i] = offsets[i] % (size_t)(file_size - access_size);
    }

    if (!read_flag) {
        to_write = (char*)malloc(access_size);
        int fd = open("/dev/urandom", O_RDONLY);
        if (fd == -1)
        {
            fprintf(stderr, "Failed to open /dev/urandom: %s\n", strerror(errno));
            exit(1);
        }
        read(fd, to_write, access_size);
    }

    struct timeval start, stop;
    gettimeofday(&start, NULL);

    for (int i = 0; i < num_threads; i++)
    {
        pthread_create(&threads[i], NULL, worker_thread, (void*) (offsets + i * num_accesses));
    }
    for (int i = 0; i < num_threads; i++)
    {
        pthread_join(threads[i], NULL);
    }

    gettimeofday(&stop, NULL);

    fprintf(stdout, "%lu", (stop.tv_sec - start.tv_sec) * 1000000 + stop.tv_usec - start.tv_usec);
    return 0;
}


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
static unsigned short rand_flag = 0;

void * worker_thread(void * arg) 
{
    int ret = 0;
    char buffer[access_size];
    size_t * offsets = (size_t *) arg;
    int fd = -1;
    
    if (rand_flag)
    {
        if (read_flag)
        {
            fd = open("file", O_RDONLY);
        } 
        else 
        {
            fd = open("file", O_WRONLY);
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
                fprintf(stderr, "ERROR: only %d B of %d B read/written: %s", ret, access_size, strerror(errno));
            }
            
        }
    }
    else
    {
        char file_name[128];
        sprintf(file_name, "thread_%u", pthread_self());
        if (read_flag)
        {
            fd = open("file", O_RDONLY);
        } 
        else 
        {
            fd = open(file_name, O_WRONLY | O_CREAT);
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
                pread(fd, &buffer, access_size, offsets[0] + i*access_size);
            }
            else
            {
                pwrite(fd, to_write, access_size, i*access_size);
            }
        }
    }
    close(fd);
}


int main(int argc, char ** argv)
{
    // parse arguments: <num_threads> <access_size(KB)> <file_size(GB)> <r/w> <r/s>
    int num_threads = atoi(argv[1]);
    access_size = 1024 * (size_t) atoi(argv[2]);
    // num_accesses = (size_t) atoi(argv[3]);
    num_accesses = (size_t) 10 * 1024 * 1024 * 1024 / access_size; 
    file_size = 1024 * 1024 * 1024 * (size_t) atoi(argv[3]);
    if (strcmp(argv[4], "r") == 0) 
    {
        read_flag = 1;
    }
    if (strcmp(argv[5], "r") == 0)
    {
        rand_flag = 1;
    }
    pthread_t threads[num_threads];
    size_t * offsets = (size_t *) malloc(sizeof(size_t)*num_threads*num_accesses);
    if (rand_flag) 
    {
        size_t ret = getrandom((void*)offsets, sizeof(size_t)*num_threads*num_accesses, 0);
        if (ret == (size_t)-1 || ret < sizeof(size_t)*num_threads*num_accesses)
        {
            fprintf(stderr, "Failed to gernerate random offsets: %s\n", strerror(errno));
            exit(1);
        }
        for (size_t i = num_threads*num_accesses; i > 0; i--)
        {
            offsets[i] = offsets[i] % (size_t)(file_size - access_size);
        }
    }
    else 
    {
        for (size_t i = 0; i < num_threads; i++)
        {
            offsets[i*num_accesses] = i * (file_size - access_size)/ num_threads;
        }
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


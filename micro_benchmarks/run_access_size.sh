#!/bin/bash

# "r" for read "w" for write
RW_FLAG=$1
# size to be read/written each time (KiB)
MAX_RW_SIZE=$2
# size of the file read/written from/to (MiB)
FILE_SIZE=$3
# number of threads to run
THREADS=$4
# number of rounds to repeat the experiment
ROUNDS=$5
OP="read"
OR="rand"

if [ ${THREADS} -gt "64" ]
then
    THREADS=64
fi
if [ $RW_FLAG = "w" ]
then
    OP="write"
fi

make micro_bench
echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
head -c ${FILE_SIZE}M </dev/urandom >file
# for (( i = 1; i <= $ROUNDS; i++ )); do
for THREADS in 1 2 4 8 16 32 64; do 
    # echo "${i}"
    echo "${THREADS}"
    for RW_SIZE in 4 8 16 32 64 128 256 512 1024; do
        echo -ne " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} KiB chunks with ${THREADS} threads...\033[0K\r"
        sync; echo 3 > /proc/sys/vm/drop_caches
        ./micro_bench ${THREADS} ${RW_SIZE} ${FILE_SIZE} ${RW_FLAG} r >> access_size_${OP}.csv
        if [ ${RW_SIZE} -lt ${MAX_RW_SIZE} ]
        then
            echo -n "," >> access_size_${OP}.csv
        else 
            echo -ne "\n" >> access_size_${OP}.csv
            break
        fi

        rm thread_* 2> /dev/null

        echo " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} KiB chunks with ${THREADS} threads - DONE."
    done
done

echo "Benchmark complete, results written to access_size_${OP}.csv"

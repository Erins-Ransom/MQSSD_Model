#!/bin/bash

# "r" for read "w" for write
RW_FLAG=$1
# "r" for random "s" for sequential access
RS_FLAG=$2
# size to be read/written each time (KiB)
RW_SIZE=$3
# size of the file read/written from/to (MiB)
FILE_SIZE=$4
# max number of threads to run
MAX_THREADS=$5
# number of rounds to repeat the experiment
ROUNDS=$6
OP="read"
OR="rand"

if [ ${MAX_THREADS} -gt "64" ]
then
    MAX_THREADS=64
fi
if [ $RW_FLAG = "w" ]
then
    OP="write"
fi
if [ $RS_FLAG = "s" ]
then
    OR="seq"
fi

# rm ${OP}.csv
make micro_bench
echo -ne " [STATUS] gernerating ${FILE_SIZE} MB file...\r"
head -c ${FILE_SIZE}M </dev/urandom >file
for (( i = 1; i <= $ROUNDS; i++ )); do
    echo "${i}"
    for k in 1 2 4 8 16 32 64; do
        echo -ne " [STATUS] ${OP}_${OR} $(( k*10 )) GiB with ${k} threads...\033[0K\r"
        sync; echo 3 > /proc/sys/vm/drop_caches
        ./micro_bench ${k} ${RW_SIZE} ${FILE_SIZE} ${RW_FLAG} ${RS_FLAG} >> num_threads_${OP}_${OR}.csv
        if [ ${k} -lt ${MAX_THREADS} ]
        then
            echo -n "," >> num_threads_${OP}_${OR}.csv
        else 
            echo -ne "\n" >> num_threads_${OP}_${OR}.csv
            break
        fi

        rm thread_* 2> /dev/null

        echo " [STATUS] num_threads_${OP}_${OR} $(( k*10 )) GiB with ${k} threads - DONE."
    done
done

echo "Benchmark complete, results written to num_threads_${OP}_${OR}.csv"

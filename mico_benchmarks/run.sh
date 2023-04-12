#!/bin/bash

# "r" for read "w" for write
RW_FLAG=$1
# "r" for random "s" for sequential access
RS_FLAG=$2
# size to be read/written each time (KiB)
RW_SIZE=$3
# number of accesses
NUM_ACCESS=$4
# size of the file read/written from/to (GiB)
FILE_SIZE=$5
# max number of threads to run
MAX_THREAS=$6
# number of rounds to repeat the experiment
ROUNDS=$7
OP="read"
OR="rand"

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
echo -ne " [STATUS] gernerating ${FILE_SIZE}GB file...\r"
if [ $RS_FLAG ]
head -c ${FILE_SIZE}G </dev/urandom >file
for (( i = 1; i <= $ROUNDS; i++)); do
    echo "${i}"
    # for k in 1 2 4 8 16 32 64; do
    for (( k=1; k <= MAX_THREADS; k = k * 2 )); do
        echo -ne " [STATUS] ${OP}_${OR} $(( k*RW_SIZE*NUM_ACCESS ))B with ${k} threads...\033[0K\r"
        sync; echo 3 > /proc/sys/vm/drop_caches
        ./micro_bench ${k} ${RW_SIZE} ${NUM_ACCESS} ${FILE_SIZE} ${RW_FLAG} ${RS_FLAG} >> ${OP}_${OR}.csv
        if [ ${k} -ne 64 ]
        then
            echo -n ", " >> ${OP}_${OR}.csv
        else 
            echo -ne "\n" >> ${OP}_${OR}.csv
        fi

        echo " [STATUS] ${OP}_${OR} $(( k*RW_SIZE*NUM_ACCESS ))B with ${k} threads - DONE."
    done
done

echo "Benchmark complete, results written to ${OP}_${OR}.csv"

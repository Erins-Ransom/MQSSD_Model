#!/bin/bash

RW_FLAG=$1
RW_SIZE=$2
FILE_SIZE=$3
ROUNDS=$4
OP="read"

if [ $RW_FLAG = "w" ]
then
    OP="write"
fi

rm ${OP}.csv
make ${OP}
echo -ne " [STATUS] gernerating ${FILE_SIZE}GB file...\r"
head -c ${FILE_SIZE}G </dev/urandom >file
# for (( k = 1; k <= $THREADS; ++k)); do
for i in {1..${ROUNDS}}; do
    for k in 1 2 4 8 16 32 64; do 
        echo -ne " [STATUS] ${OP} $(( k*10)) with ${k} threads...\033[0K\r"
        sync; echo 3 > /proc/sys/vm/drop_caches
        ./${OP} ${k} ${RW_SIZE} >> ${OP}.csv
        if [${k} -eq ${ROUNDS}]
        then
            echo -n ", " >> ${OP}.csv
        else 
            echo -ne "\n" >> ${OP}.csv
        fi

        echo " [STATUS] ${OP} $(( k*10 ))GB with ${k} threads - DONE."
    done

done

echo "Benchmark complete, results written to ${OP}.csv"

#!/bin/bash

RW_FLAG=$1
THREADS=$2
RW_SIZE=$3
FILE_SIZE=$(( THREADS*RW_SIZE ))
OP="read"

if [ $RW_FLAG = "w" ]
then
    OP="write"
fi

rm ${OP}.csv
make ${OP}
echo -ne " [STATUS] gernerating ${FILE_SIZE}GB file...\r"
head -c ${FILE_SIZE}G </dev/urandom >file
for (( k = 1; k <= $THREADS; ++k)); do
    echo -ne " [STATUS] ${OP} $(( k*RW_SIZE ))GB with ${k} threads...\033[0K\r"
    ./${OP} ${THREADS} ${RW_SIZE} >> ${OP}.csv
    echo -n ", " >> ${OP}.csv
    echo " [STATUS] ${OP} $(( k*RW_SIZE ))GB with ${k} threads - DONE."
done

echo "Benchmark complete, results written to ${OP}.csv"

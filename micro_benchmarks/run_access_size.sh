#!/bin/bash

# "r" for read "w" for write
# RW_FLAG=$1
# size to be read/written each time (KiB)
# MAX_RW_SIZE=$2
MAX_RW_SIZE=1024 # 1 MiB
# size of the file read/written from/to (MiB)
# FILE_SIZE=$3
FILE_SIZE=20480 # 20 GiB
# number of threads to run
# THREADS=$4
# number of rounds to repeat the experiment
# ROUNDS=$5
OP="read"

# if [ ${THREADS} -gt "64" ]
# then
#     THREADS=64
# fi
# if [ $RW_FLAG = "w" ]
# then
#     OP="write"
# fi

make micro_bench
for dev in "5" "4" "3"; do
    FILE="dev_${dev}/file"
    # echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
    # head -c ${FILE_SIZE}M </dev/urandom >${FILE}

    for OP in "read" "write"; do
        OUT="results/gen_${dev}/access_size_${OP}-$(date +%Y-%m-%d-%T).csv"
        if [ ${OP} = "read" ]
        then 
            RW_FLAG="r"
        else
            RW_FLAG="w"
        fi
        # for (( i = 1; i <= $ROUNDS; i++ )); do
        for THREADS in 1 2 4 8 16 32 64; do 
            echo "${THREADS}"
            for RW_SIZE in 4 8 16 32 64 128 256 512 1024; do
                echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
                head -c ${FILE_SIZE}M </dev/urandom >${FILE}
                echo -ne " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} KiB chunks with ${THREADS} threads...\033[0K\r"
                sync; echo 3 > /proc/sys/vm/drop_caches
                ./micro_bench ${FILE} ${THREADS} ${RW_SIZE} ${FILE_SIZE} ${RW_FLAG} >> ${OUT}
                if [ ${RW_SIZE} -lt ${MAX_RW_SIZE} ]
                then
                    echo -n "," >> ${OUT}
                else 
                    echo -ne "\n" >> ${OUT}
                    break
                fi

                rm thread_* 2> /dev/null

                echo " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} KiB chunks with ${THREADS} threads - DONE."
            done
        done

        echo "${OP} benchmark on device ${dev} complete, results written to ${OUT}"
    done

done
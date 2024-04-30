#!/bin/bash

USER="wintermute"
# "r" for read "w" for write
# RW_FLAG=$1
# size to be read/written each time (KiB)
# MAX_RW_SIZE=$2
MAX_RW_SIZE=1048576 # 1 MiB
# size of the file read/written from/to (B)
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
    echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
    head -c ${FILE_SIZE}M </dev/urandom >${FILE}

    for OP in "_read" "_write"; do
        if [ ${dev} == "5" ]
        then
            OUT_DIR="results/Crucial/${OP}"
        elif [ ${dev} == "4" ]
        then
            OUT_DIR="results/Samsung/${OP}"
        elif [ ${dev} == "3" ]
        then
            OUT_DIR="results/PNY/${OP}"
        else
            echo "Invalid dev"
            exit 1
        fi
        OUT="${OUT_DIR}/access_size${OP}-$(date +%Y-%m-%d-%T).csv"
        if [ ${OP} = "read" ]
        then 
            RW_FLAG="r"
        else
            RW_FLAG="w"
        fi
        # for (( i = 1; i <= $ROUNDS; i++ )); do
        for THREADS in 1 2 4 8 16 32 64 128; do 
            echo "${THREADS}"
            for RW_SIZE in 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288 1048576 2097152; do
            # for RW_SIZE in 2097152; do
                echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
                head -c ${FILE_SIZE}M </dev/urandom >${FILE}
                echo -ne " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} KiB chunks with ${THREADS} threads...\033[0K\r"
                sync; echo 3 > /proc/sys/vm/drop_caches

                if [ ${dev} == "5" ]
                then
                    DEVICE="/dev/nvme0n1"
                elif [ ${dev} == "4" ]
                then
                    DEVICE="/dev/nvme2n1"
                elif [ ${dev} == "3" ]
                then
                    DEVICE="/dev/nvme1n1"
                else
                    echo "Invalid dev"
                    exit 1
                fi
                
                blktrace "${DEVICE}" -D "${OUT_DIR}" -a issue -a complete &
                BTRACE_PID=$!
                ./micro_bench ${FILE} ${THREADS} ${RW_SIZE} ${FILE_SIZE} ${RW_FLAG} >> ${OUT}
                kill ${BTRACE_PID}
                
                if [ ${RW_SIZE} -lt ${MAX_RW_SIZE} ]
                then
                    echo -n "," >> ${OUT}
                else 
                    echo -ne "\n" >> ${OUT}
                    break
                fi

                rm thread_* 2> /dev/null

                echo " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} B chunks with ${THREADS} threads - DONE."
            done
        done

        echo "${OP} benchmark on device ${dev} complete, results written to ${OUT}"
        chown ${USER} ${OUT}
    done

done

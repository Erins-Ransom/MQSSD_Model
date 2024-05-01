#!/bin/bash

USER="wintermute"
MAX_RW_SIZE=1048576 # 1 MiB
FILE_SIZE=20480 # 20 GiB
OP="read"
BLKTRACE="True"

make micro_bench
# for (( i = 1; i <= $ROUNDS; i++ )); do
    # for dev in "Crucial" "Samsung" "PNY"; do
    for dev in "Samsung"; do
        FILE="../dev/${dev}/file"
        # echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
        # head -c ${FILE_SIZE}M </dev/urandom >${FILE}

        if [ ${dev} == "Crucial" ]
        then
            DEVICE="/dev/nvme0n1"
        elif [ ${dev} == "Samsung" ]
        then
            DEVICE="/dev/nvme2n1"
        elif [ ${dev} == "PNY" ]
        then
            DEVICE="/dev/nvme1n1"
        else
            echo "Invalid dev"
            exit 1
        fi

        if [ ${BLKTRACE} == "True" ]
        then
            BLK_DIR="results/${dev}/blktrace-$(date +%Y-%m-%d-%T)"
        fi

        for OP in "_read" "_write"; do
            if [ ${BLKTRACE} == "True" ]
            then
                OUT_DIR="${BLK_DIR}/${OP}"
                OUT="${OUT_DIR}/times.csv"
            else
                OUT_DIR="results/${dev}/${OP}"
                OUT="${OUT_DIR}/times-$(date +%Y-%m-%d-%T).csv"
            fi

            mkdir -p ${OUT_DIR}

            if [ ${OP} = "_read" ]
            then 
                RW_FLAG="r"
            else
                RW_FLAG="w"
            fi
            
            for THREADS in 1 2 4 8 16 32 64 128; do 
                echo "${THREADS}"
                for RW_SIZE in 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288 1048576 2097152; do
                    echo -ne " [STATUS] gernerating ${FILE_SIZE} MiB file...\r"
                    head -c ${FILE_SIZE}M </dev/urandom >${FILE}
                    echo -ne " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} KiB chunks with ${THREADS} threads...\033[0K\r"
                    sync; echo 3 > /proc/sys/vm/drop_caches

                    
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

                    blkparse nvme2n1 -o "${OUT_DIR}/${THREADS}_${RW_SIZE}_trace"
                    # tar -czvf blktrace.tgz nvme2n1.blktrace.*
                    rm nvme2n1.blktrace.*

                    echo " [STATUS] ${OP} $(( THREADS*10 )) GiB in ${RW_SIZE} B chunks with ${THREADS} threads - DONE."
                done
            done
            echo "${OP} benchmark on device ${dev} complete, results written to ${OUT}"
            chown ${USER} -R ${OUT_DIR}
        done
    done
done

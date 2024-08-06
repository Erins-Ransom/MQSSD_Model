#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

flushthreads_arr=(1)
compthreads_arr=(10)
fanout_arr=(10)
dynamic_level_arr=("1")
compstyle_arr=("Level")
nreaders_arr=(10)

################################################################

REPO_DIR="$(pwd)"
EXP_BIN="$REPO_DIR/rocksdb-8.6.7/build/mqssd/mqssd"
READER_BIN="$REPO_DIR/rocksdb-8.6.7/build/mqssd/reader"
RESULTS_DIR="$REPO_DIR/results"
DEV_DIR="$REPO_DIR/../dev/Samsung"
WORKL_BIN="$REPO_DIR/../workload_gen"
DATA_DIR="$REPO_DIR/data"

nkeys=100000 #100000000
nqueries=1000000 #1000000


# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"

run_readers() {
    pids=()

    # Run readers in parallel (hopefully)
    for i in `seq $nrdrs`; do
        echo $i; $READER_BIN "$DATA_DIR/queries/$nrdrs/$nqueries/$i" "$i"
        echo $!
    done
    
    for pid in $pids; do
        wait $pid
    done
}

experiment() {
    res="$resdir/exp.txt"
    touch "$res"
    echo -e "Number of Keys:\t$nkeys" >> "$res"
    echo -e "Number of Queries:\t$nqueries" >> "$res"
    echo -e "Compaction Style:\t$compstyle" >> "$res"
    echo -e "Flush Threads:\t$ft" >> "$res"
    echo -e "Compaction Threads:\t$ct" >> "$res"
    echo -e "Fanout:\t\t$fan" >> "$res"
    echo -e "Dynamic Level:\t$dl" >> "$res"
    echo -e "Number of Readers:\t$nrdrs" >> $res
    echo -e "\n" >> "$res"

    if [ ! -e "$DATA_DIR/keys/1/$nkeys" ]; then
        echo "Generating $DATA_DIR/keys/1/$nkeys"
        $WORKL_BIN $DATA_DIR/keys/ "$nkeys" "1"
    fi

    if [ ! -e "$DATA_DIR/queries/$nrdrs/$nqueries" ]; then
        echo "Generating $DATA_DIR/queries/$nrdrs/$nqueries"
        $WORKL_BIN $DATA_DIR/queries/ "$nqueries" "$nrdrs"
    fi

    # Populate the database
    cd "$expdir"
    $EXP_BIN $DATA_DIR $nkeys $nqueries $ft $ct $fan $compstyle $dl 32 >> "$res"

    # blktrace /dev/nvme2n1 -D "$resdir" -a issue -a complete &
    # starttime=$(expr `date +%s%N` / 1000)
    # echo -e "BLKTRACE START TIME: $starttime\n\n" >> "$res"
    # BTRACE_PID=$!

    # time run_readers
    $READER_BIN $DATA_DIR/keys/1/$nkeys/0 >> "$res"
    # seq 0 $(( $nrdrs - 1 )) | parallel $READER_BIN $DATA_DIR/queries/$nrdrs/$nqueries/{} >> "$res"

    # kill ${BTRACE_PID}

    rm -rf $expdir

    # cd "$resdir"

    # blkparse nvme2n1 -o "trace" >> "$res"
    # tar -czvf blktrace.tgz nvme2n1.blktrace.*
    # rm nvme2n1.blktrace.*

    # chown wintermute -R "$resdir"
}

for compstyle in "${compstyle_arr[@]}"; do

    if [[ "$compstyle" == "Level" ]]; then

        for ft in "${flushthreads_arr[@]}"; do
        for ct in "${compthreads_arr[@]}"; do
        for fan in "${fanout_arr[@]}"; do
        for dl in "${dynamic_level_arr[@]}"; do
        for nrdrs in "${nreaders_arr[@]}"; do

        resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
        expdir=$(mktemp -d $DEV_DIR/$(date +%Y-%m-%d-%T)XXX)
        experiment

        done
        done
        done
        done
        done

    elif [[ "$compstyle" == "Universal" ]]; then
        
        for ft in "${flushthreads_arr[@]}"; do
        for ct in "${compthreads_arr[@]}"; do
        for fan in "${fanout_arr[@]}"; do
        for nrdrs in "${nreaders_arr[@]}"; do

        dl="0"
        resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
        expdir=$(mktemp -d $DEV_DIR/$(date +%Y-%m-%d-%T)XXX)
        experiment

        done
        done
        done
        done

    fi

done
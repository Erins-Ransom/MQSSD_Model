#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

flushthreads_arr=(1) #2 3 4)
compthreads_arr=(1 2 4 8 16 32)
# maxsubcomp_arr=(16) #1 2 4 8)  now set to same value as compthreads
fanout_arr=(2 4 8 16)
nrunsuniversal_arr=(2 4 8 16)
dynamic_level_arr=("0" "1")
# compstyle_arr=("Level" "Universal")
compstyle_arr=("Universal")
filesize_arr=(32)           # in MB

################################################################

REPO_DIR="$(pwd)"
EXP_BIN="$REPO_DIR/rocksdb-8.6.7/build/mqssd/mqssd"
RESULTS_DIR="$REPO_DIR/results"
DEV_DIR="$REPO_DIR/../dev/Samsung"
WORKL_BIN="$REPO_DIR/../workload_gen"
DATA_DIR="$REPO_DIR/data"

nkeys=100000000
nqueries=1000000


# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"

experiment() {
    res="$resdir/exp.txt"
    touch "$res"
    echo -e "Number of Keys:\t$nkeys" >> "$res"
    echo -e "Number of Queries:\t$nqueries" >> "$res"
    echo -e "Target File Size:\t$fs MB" >> "$res"
    echo -e "Compaction Style:\t$compstyle" >> "$res"
    echo -e "Flush Threads:\t$ft" >> "$res"
    echo -e "Compaction Threads:\t$ct" >> "$res"
    echo -e "Fanout:\t\t$fan" >> "$res"
    echo -e "Target Number of Runs:\t$nr" >> "$res" 
    echo -e "Dynamic Level:\t$dl" >> "$res"
    echo -e "\n" >> "$res"

    if [ ! -e "$DATA_DIR/keys/1/$nkeys" ]; then
        echo "Generating $DATA_DIR/keys/1/$nkeys"
        $WORKL_BIN $DATA_DIR/keys/ "$nkeys" "1"
    fi

    # TODO: Remove hardcoded 1
    if [ ! -e "$DATA_DIR/queries/1/$nqueries" ]; then
        echo "Generating $DATA_DIR/queries/1/$nqueries"
        $WORKL_BIN $DATA_DIR/queries/ "$nqueries" "1"
    fi

    cd "$expdir"
    # blktrace /dev/nvme2n1 -D "$resdir" -a issue -a complete &
    # starttime=$(expr `date +%s%N` / 1000)
    # echo -e "BLKTRACE START TIME: $starttime\n\n" >> "$res"
    # BTRACE_PID=$!
    $EXP_BIN $DATA_DIR $nkeys $nqueries $ft $ct $fan $compstyle $dl $nr $fs >> "$res"
    # kill ${BTRACE_PID}

    cp db/LOG "$resdir"
    rm -rf $expdir

    # cd "$resdir"

    # blkparse nvme2n1 -o "trace" >> "$res"
    # tar -czvf blktrace.tgz nvme2n1.blktrace.*
    # rm nvme2n1.blktrace.*

    # chown wintermute -R "$resdir"
}

for compstyle in "${compstyle_arr[@]}"; do


    if [[ "$compstyle" == "Level" ]]; then

        for fs in "${filesize_arr[@]}"; do 
        for ft in "${flushthreads_arr[@]}"; do
        for ct in "${compthreads_arr[@]}"; do
        for fan in "${fanout_arr[@]}"; do
        for dl in "${dynamic_level_arr[@]}"; do

        nr="N/A"
        resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
        expdir=$(mktemp -d $DEV_DIR/$(date +%Y-%m-%d-%T)XXX)
        experiment

        done
        done
        done
        done
        done

    elif [[ "$compstyle" == "Universal" ]]; then
        
        for fs in "${filesize_arr[@]}"; do
        for ft in "${flushthreads_arr[@]}"; do
        for ct in "${compthreads_arr[@]}"; do
        for nr in "${nrunsuniversal_arr[@]}"; do

        fan="N/A"
        dl="N/A"
        resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
        expdir=$(mktemp -d $DEV_DIR/$(date +%Y-%m-%d-%T)XXX)
        experiment

        done
        done
        done
        done

    fi

done
#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

batch_code="0004"
ntrials=4

################################################################

# Database Configuration

compthreads_arr=(1 3 7 15 31)
fanout_arr=(2 4 8 16)
dynamic_level_arr=("1") # "0")
compstyle_arr=("Level" "Universal")
filesize_arr=(32 64 128) # in MB

################################################################

# Benchmark Parameters

write_benchmark_arr=("filluniquerandomdeterministic")
nkeys_arr=(10000000)

read_benchmark_arr=("readrandom")
nqueries_arr=(10000000)
readthreads_arr=(8)

################################################################

REPO_DIR="$(pwd)"
INIT_BIN="$REPO_DIR/rocksdb-8.6.7/build/mqssd/dbb"
DB_BENCH="$REPO_DIR/rocksdb-8.6.7/build/db_bench"
RESULTS_DIR="$REPO_DIR/results"
DEV_DIR="$REPO_DIR/../dev/Samsung"

# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"

################################################################

experiment() {
    resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
    expdir=$(mktemp -d $DEV_DIR/$(date +%Y-%m-%d-%T)XXX)
    
    res="$resdir/exp.txt"
    touch "$res"

    echo -e "Batch Code:\t\t$batch_code" >> "$res"
    echo -e "Target File Size:\t$fs MB" >> "$res"
    echo -e "Compaction Style:\t$compstyle" >> "$res"
    echo -e "Compaction Threads:\t$ct" >> "$res"
    echo -e "Fanout:\t\t$fan" >> "$res"
    echo -e "Dynamic Level:\t$dl" >> "$res"
    echo -e "\n" >> "$res"

    cd "$expdir"
    
    # Initialize  and configure database
    $INIT_BIN $ct $fan $compstyle $dl $fs

    # Populate database
    $DB_BENCH --use_existing_db=true --benchmarks="$wbm,waitforcompaction,levelstats" --num=$nkeys >> "$res"
    
    # Read to database
    $DB_BENCH --use_existing_db=true --benchmarks=$rbm --reads=$nqueries --threads=$rt --async_io=true >> "$res"

    rm -rf $expdir
}

for i in `seq $ntrials`; do 
    for compstyle in "${compstyle_arr[@]}"; do

        if [[ "$compstyle" == "Level" ]]; then

            for fs in "${filesize_arr[@]}"; do 
            for ct in "${compthreads_arr[@]}"; do
            for fan in "${fanout_arr[@]}"; do
            for dl in "${dynamic_level_arr[@]}"; do

            experiment

            done
            done
            done
            done

        elif [[ "$compstyle" == "Universal" ]]; then
            
            for fs in "${filesize_arr[@]}"; do
            for ct in "${compthreads_arr[@]}"; do
            for fan in "${fanout_arr[@]}"; do

            dl="N/A"
            experiment

            done
            done
            done

        fi

    done
done

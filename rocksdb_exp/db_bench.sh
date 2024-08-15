#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

batch_code="test"
ntrials=1

################################################################

# Database Configuration

compthreads_arr=(15) #1 3 7 15 31)
fanout_arr=(10) # 2 4 8 16)
dynamic_level_arr=("true") # "0")
compstyle_arr=("Level") #"Universal")
filesize_arr=(32) #64 128) # in MB

################################################################

# Benchmark Parameters

write_benchmark_arr=("fillrandom")
nkeys_arr=(1000000)

read_benchmark_arr=("readrandom")
nqueries_arr=(1000000)
readthreads_arr=(2 16)

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
    
    echo -e "Write Benchmark:\t$wbm" >> "$res"
    echo -e "Number of Keys:\t$nk" >> "$res"

    echo -e "\n" >> "$res"

    cd "$expdir"
    
    # Initialize and configure database
    # $INIT_BIN

    # Populate database
    if [[ "$compstyle" == "Level" ]]; then

        num_levels=9
        $DB_BENCH --benchmarks="$wbm,waitforcompaction" --num=$nk \
                  \
                  --num_levels=$num_levels \
                  --compaction_style=0 \
                  --level_compaction_dynamic_level_bytes=$dl \
                  --target_file_size_multiplier=1 \
                  --max_bytes_for_level_base=$((4*fs*1048576)) \
                  --max_bytes_for_level_multiplier=$fan \
                  --level0_file_num_compaction_trigger=4 \
                  \
                  --write_buffer_size=$((fs*1048576)) \
                  --target_file_size_base=$((fs*1048576)) \
                  --max_background_jobs=$((ct+1)) \
                  --subcompactions=$((ct+1)) \
                  --use_direct_reads=true \
                  --use_direct_io_for_flush_and_compaction=true \
                  --compression_type=none \
                  >> "$res"
    
    elif [[ "$compstyle" == "Universal" ]]; then

        num_levels=$((fan*5))
        $DB_BENCH --benchmarks="$wbm,waitforcompaction" --num=$nk \
              \
              --num_levels=$num_levels \
              --compaction_style=1 \
              --periodic_compaction_seconds=0 \
              --level0_file_num_compaction_trigger=$fan \
              --universal_max_size_amplification_percent=$(( 100 * ((fan-1) + fan / (fan-1)) )) \
              --universal_size_ratio=1 \
              --universal_min_merge_width=$fan \
              --universal_max_merge_width=$fan \
              \
              --write_buffer_size=$((fs*1048576)) \
              --target_file_size_base=$((fs*1048576)) \
              --max_background_jobs=$((ct+1)) \
              --subcompactions=$((ct+1)) \
              --use_direct_reads=true \
              --use_direct_io_for_flush_and_compaction=true \
              --compression_type=none \
              >> "$res"
    fi

    # Warm cache

    # Read database
    # TODO: pass seed here
    for rbm in "${read_benchmark_arr[@]}"; do
    for nq in "${nqueries_arr[@]}"; do
    for rt in "${readthreads_arr[@]}"; do

    echo -e "\n" >> "$res"
    echo -e "Read Benchmark:\t$rbm" >> "$res"
    echo -e "Number of Queries:\t$nq" >> "$res"
    echo -e "Number of Read Threads:\t$rt" >> "$res"
    echo -e "\n" >> "$res"
    
    $DB_BENCH --use_existing_db=true --benchmarks=$rbm \
              --reads=$nq --threads=$rt --num_levels=$num_levels \
              \
              --async_io=true --use_direct_reads=true \
              --compression_type=none >> "$res"

    done
    done
    done

    rm -rf $expdir
}

for i in `seq $ntrials`; do 
    for compstyle in "${compstyle_arr[@]}"; do
    for wbm in "${write_benchmark_arr[@]}"; do
    for nk in "${nkeys_arr[@]}"; do

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
    done
done

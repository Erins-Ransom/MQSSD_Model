#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

threads_arr=(4 6 8 10 12)
fanout_arr=(10)

# threads_arr=(1 4 8 12)
# fanout_arr=(5 10 15)

################################################################

REPO_DIR="$(pwd)"
EXP_BIN="$REPO_DIR/rocksdb-8.6.7/build/mqssd/mqssd"
RESULTS_DIR="$REPO_DIR/results"
DEV_4_DIR="$REPO_DIR/micro_benchmarks/dev_4"
WORKL_BIN="$REPO_DIR/workload_gen"
DATA_DIR="$REPO_DIR/data"

nkeys=50000000
nqueries=1000000

# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"

experiment() {
    res="$resdir/exp.txt"
    touch "$res"
    echo -e "Number of Keys:\t$nkeys" >> "$res"
    echo -e "Number of Queries:\t$nqueries" >> "$res"
    echo -e "Threads:\t$t" >> "$res"
    echo -e "Fanout:\t\t$f" >> "$res"
    echo -e "\n" >> "$res"

    if [ ! -e "$DATA_DIR/keys/$nkeys.txt" ]; then
        echo "Generating $DATA_DIR/keys/$nkeys.txt"
        $WORKL_BIN $DATA_DIR/keys "$nkeys"
    fi

    if [ ! -e "$DATA_DIR/queries/$nqueries.txt" ]; then
        echo "Generating $DATA_DIR/queries/$nqueries.txt"
        $WORKL_BIN $DATA_DIR/queries "$nqueries"
    fi

    cd "$expdir"
    blktrace /dev/nvme2n1 -D "$resdir" -a issue -a complete &
    starttime=$(expr `date +%s%N` / 1000)
    echo -e "BLKTRACE START TIME: $starttime\n\n" >> "$res"
    BTRACE_PID=$!
    $EXP_BIN $DATA_DIR $nkeys $nqueries $t $f >> "$res"
    kill ${BTRACE_PID}

    cp db/LOG "$resdir"
    rm -rf $expdir

    cd "$resdir"

    blkparse nvme2n1 -o "trace" >> "$res"
    tar -czvf blktrace.tgz nvme2n1.blktrace.*
    rm nvme2n1.blktrace.*

    chown wintermute -R "$resdir"
}

for t in "${threads_arr[@]}"; do
for f in "${fanout_arr[@]}"; do

resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
expdir=$(mktemp -d $DEV_4_DIR/$(date +%Y-%m-%d-%T)XXX)
experiment

done
done
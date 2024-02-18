#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

threads_arr=(2 4 6 8 10 12)
fanout_arr=(5 10 15)

################################################################

REPO_DIR="$(pwd)"
EXP_BIN="$REPO_DIR/rocksdb-8.6.7/build/mqssd/mqssd"
RESULTS_DIR="$REPO_DIR/results"

# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"

experiment() {
    cd "$expdir"
    touch ./exp.txt
    echo -e "Threads:\t$t" >> ./exp.txt
    echo -e "Fanout:\t\t$f" >> ./exp.txt
    echo -e "\n" >> ./exp.txt

    $EXP_BIN $t $f >> ./exp.txt

    rm -rf ./db/
}

for t in "${threads_arr[@]}"; do
for f in "${fanout_arr[@]}"; do

expdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
experiment

done
done
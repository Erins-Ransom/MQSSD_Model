#!/bin/bash

set -o errexit          # Exit if a command fails 
set -o nounset          # Throw error when accessing an unset variable
cd "$(dirname "$0")"    # Change to directory of this script

IFS=""

REPO_DIR="$(pwd)"
DB_BENCH="$REPO_DIR/rocksdb-8.6.7/build/db_bench"
RESULTS_DIR="$REPO_DIR/results"
DEV_DIR="$REPO_DIR/../dev/Samsung"

# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"

resdir=$(mktemp -d $RESULTS_DIR/$(date +%Y-%m-%d-%T)XXX)
expdir=$(mktemp -d $DEV_DIR/$(date +%Y-%m-%d-%T)XXX)

res="$resdir/exp.txt"
touch "$res"

cd "$expdir"
$DB_BENCH --benchmarks="filluniquerandomdeterministic" --num_levels=3 --num=1000000 --compression_type="none" --disable_auto_compactions=true
$DB_BENCH --benchmarks="readrandom" --use_existing_db=true --reads=6250 --threads=16 --compression_type="none"
rm -rf $expdir
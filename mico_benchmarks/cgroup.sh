#!/bin/bash

FILE="/sys/fs/cgroup/bench"

if test -f $FILE; then
    # create our control group for benchmarking
    mkdir /sys/fs/cgroup/bench

    # set the memory limit to 2GB
    echo 2147483648 > /sys/fs/cgroup/bench/memory.high
fi

# add the current shell to the cgroup
echo $$ >> /sys/fs/cgroup/bench/cgroup.procs

# execute the benchmark in the cgroup
./run.sh $1 $2 $3 $4 $5 $6 $7
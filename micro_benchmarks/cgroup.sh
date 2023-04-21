#!/bin/bash

DIR="/sys/fs/cgroup/bench"

if [ ! -d $DIR ]; then
    # create our control group for benchmarking
    mkdir $DIR

    # set the memory limit to 2GB
    echo 2147483648 > $DIR/memory.high
fi

# add the current shell to the cgroup
echo $$ >> $DIR/cgroup.procs

# execute new shell within the cgroup
/bin/bash
from datetime import datetime, timedelta
from collections import defaultdict

import matplotlib.pyplot as plt
import json
import sys
from tqdm import tqdm

TRACE_FILE = sys.argv[1]

# Assumption: Only 1 "IO" is happening at once for each thread
# Observed: Sequential and Random Write requests are issued in parallel from the same thread

num_ios = 0
# [
#    (timestamp, num_ios),
#    (timestamp, num_ios),
# ]
timestamps_x = []
ios_y = []


VID = 0
pids = {}

# (0, read), (0, write), (1, read), (1 write)

reqs = {} # (start_addr, offset): VID

# 1st Dimension: (pid, write)
# 2nd Dimension: different IOs / different start address

# TODO: Clean up the old sets?
# [[set(requests), set(requests)], ]
ios = []

# [{last_addr: idx}, {}]
last_addr = []

# D 1 + 1 (pid, write, 1, 2)
# D 2 + 1 (pid, write, 3)
# D 3 + 1 (pid, write, 4)
# C 1 + 1

with open(f"{TRACE_FILE}", "r") as f:
    for lineno, line in tqdm(enumerate(f)):
        if line.startswith("CPU"):
            break

        if line != "\n" and "kworker" not in line:
            tokens = line.split()
            time = tokens[3]
            pid = int(tokens[4])
            event = tokens[5]   # D (issued) or C (completed)
            rw = tokens[6]      # R (read) or W (write)
            start_addr = int(tokens[7])

            write = "W" in tokens[6]
            read = "R" in tokens[6]

            if not write ^ read or start_addr == 0:
                print(line)
                continue
            
            offset = int(tokens[9])
            name = tokens[10]

            if event == "D":
                if pid not in pids:
                    pids[pid] = VID
                    VID += 1
                    ios.append([])
                    ios.append([])
                    last_addr.append(dict())
                    last_addr.append(dict())

                idx = (pids[pid] * 2) + (1 if write else 0)

                # New IO for (pid, write)
                if start_addr not in last_addr[idx]:
                    num_ios += 1
                    timestamps_x.append(datetime.fromtimestamp(float(time)))
                    ios_y.append(num_ios)

                    # Add a new mapping (start_addr: sub-list index)
                    last_addr[idx][start_addr] = len(ios[idx])

                    # Add a new set to track requests for this IO
                    ios[idx].append(set())

                # else:
                    # if last_addr[(pid, write)] != 0 and last_addr[(pid, write)] != int(start_addr):
                    #     print(last_addr[(pid, write)])
                    #     print(start_addr)
                    #     print(line)
                    #     print(ios[(pid, write)])
                    #     exit(1)
                        # assert last_addr[(pid, write)] == int(start_addr)

                sub_idx = last_addr[idx][start_addr]
                request = (start_addr, offset)
                assert request not in ios[idx][sub_idx]

                # Add request to specific IO tracking
                ios[idx][sub_idx].add(request)

                # Update last_addr with start_addr + offset
                last_addr[idx].pop(start_addr)
                last_addr[idx][start_addr + offset] = sub_idx
                
                # Update request tracking
                reqs[request] = (idx, sub_idx)
                                
            elif event == "C":
                request = (start_addr, offset)

                # Look up request
                if request in reqs:
                    idx, sub_idx = reqs[request]
                    
                    if not ((read and idx % 2 == 0) or (write and idx % 2 == 1)):
                        print(read)
                        print(write)
                        print(idx)
                        print(line)
                        exit(1)
                    
                    # Remove request from specific IO tracking
                    ios[idx][sub_idx].remove(request)

                    # Remove request from request tracking
                    reqs.pop(request)

                    # Check if no more requests pending for IO
                    if not ios[idx][sub_idx]:
                        num_ios -= 1
                        timestamps_x.append(datetime.fromtimestamp(float(time)))
                        ios_y.append(num_ios)

                        for k, v in last_addr[idx].items():
                            if v == sub_idx:
                                del last_addr[idx][k]
                                break
            else:
                continue

print(len(timestamps_x))
print(ios_y[-1])
print(reqs)
print(len(pids))

plt.scatter(timestamps_x, ios_y, marker=".", alpha=0.2)
plt.gcf().autofmt_xdate()
# plt.xlim([fl_start[0] + timedelta(minutes=1), fl_start[0] + timedelta(minutes=2)])
plt.savefig(f"{TRACE_FILE}.png")
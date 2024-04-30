from datetime import datetime, timedelta
from collections import defaultdict

import matplotlib.pyplot as plt
import json
import sys
from tqdm import tqdm

DIR = sys.argv[1]

blktrace_start = None
with open(f"{DIR}/exp.txt", "r") as f:
    for line in f:
        if "BLKTRACE START TIME" in line:
            tokens = line.split(": ")
            blktrace_start = int(tokens[1])
            break

print(blktrace_start)

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

with open(f"{DIR}/trace", "r") as f:
    for lineno, line in tqdm(enumerate(f), total=89931849):
        if lineno == 20000000:
            print(line)
            break

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
                # print(line)
                continue
            
            offset = int(tokens[9])
            name = tokens[10]

            if event == "D" and (name == "[rocksdb:high]" or name == "[rocksdb:low]"):
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
                    timestamps_x.append(datetime.fromtimestamp(float(time) + (blktrace_start / (10**6))))
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
                        timestamps_x.append(datetime.fromtimestamp(float(time) + (blktrace_start / (10**6))))
                        ios_y.append(num_ios)

                        for k, v in last_addr[idx].items():
                            if v == sub_idx:
                                del last_addr[idx][k]
                                break

            else:
                continue

for i in range(len(ios_y)):
    ios_y[i] -= 0.5
# print(len(timestamps_x))
# print(ios_y[-1])
# print(reqs)
# print(len(pids))

# for i in range(1, len(timestamps_x)):
#     print(timestamps_x[i] - timestamps_x[i-1])

# timestamps_x.insert(0, timestamps_x[0])
# ios_y.insert(0, 0)


# avg_ts = []
# avg_ios = []

# start = 0
# durations = []
# for i in range(len(timestamps_x)):
#     if timestamps_x[i] - timestamps_x[start] > timedelta(seconds=0.1):
#         avg_ts.append(timestamps_x[start] + (timestamps_x[i-1] - timestamps_x[start]) / 2)

#         period = timestamps_x[i-1] - timestamps_x[start]
#         ios_sum = 0
#         for j in range(start, i):
#             ios_sum += ios_y[j] * (durations[j - start] / period)

#         avg_ios.append(ios_sum / (i - 1 - start))

#         durations = []
#         start = i

#     durations.append(timestamps_x[i] - timestamps_x[i-1])
    

# avg_ts.append(start + (timestamps_x[i] - start) / 2)
# avg_ios.append(ios_sum / count)

# plt.scatter(avg_ts, avg_ios, marker=".", alpha=0.8)
plt.scatter(timestamps_x, ios_y, marker=".", alpha=0.2)
plt.gcf().autofmt_xdate()
# plt.xlim([fl_start[0] + timedelta(minutes=1), fl_start[0] + timedelta(minutes=2)])
plt.savefig(f"{DIR}/trace.png")


fl_start = []
fl_end = []
fl_threads = []

cmp_start = []
cmp_end = []
cmp_threads = []

with open(f"{DIR}/LOG", "r") as f:
    for line in f:
        if "Flush lasted" in line:
            tokens = line.split()
            end_time = datetime.strptime(tokens[0], "%Y/%m/%d-%H:%M:%S.%f")
            duration = timedelta(microseconds=int(tokens[8]))
            thread = tokens[1]
            
            fl_start.append(end_time - duration)
            fl_end.append(end_time)
            fl_threads.append(thread)

        elif "compaction_finished" in line:
            tokens = line.split()
            thread = tokens[1]
            log = json.loads(line[line.index("{"):])
            end_time = datetime.fromtimestamp(log["time_micros"] / 1000000)
            duration = timedelta(microseconds=log["compaction_time_micros"])

            cmp_start.append(end_time - duration)
            cmp_end.append(end_time)
            cmp_threads.append(thread)


plt.hlines(y=fl_threads, xmin=fl_start, xmax=fl_end, color="green")
plt.hlines(y=cmp_threads, xmin=cmp_start, xmax=cmp_end, color="green")
plt.scatter(fl_start, fl_threads, marker="o", alpha=0.8)
plt.scatter(cmp_start, cmp_threads, marker="o", alpha=0.8)
# plt.scatter(cmp_end, cmp_threads)
plt.gcf().autofmt_xdate()
plt.xlim([fl_start[0] - timedelta(seconds=15), fl_start[0] + timedelta(minutes=10)])
plt.savefig(f"{DIR}/test.png")


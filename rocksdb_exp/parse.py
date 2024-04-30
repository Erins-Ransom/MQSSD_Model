import random
from collections import defaultdict

lines = []
pids = defaultdict(int)

with open("trace", 'r') as f:
    for line in f:
        if line.startswith("CPU"):
            break

        if line != "\n":
            cols = line.split()

            pid = cols[4]
            pids[pid] += 1

            if pid == "0":
                lines.append(line)

print(pids)
print(random.sample(lines, 20))
print(len(lines))
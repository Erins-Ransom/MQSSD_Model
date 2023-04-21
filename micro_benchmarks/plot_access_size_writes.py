#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

div = 1000000
X = np.array([1024, 512, 256, 128, 64, 32, 16, 8, 4])
num_accesses = np.array([10 * 1024 * 1024 / x for x in X])

write_1 = [ 436602397,283747339,117798463,76703769,52341773,37885014,28017720,26049917,21815967 ]
write_2 = [ ]
write_4 = [ 1679058391,1027773281,560814878,323728925,223598178,193814229,156318514,137191191,118361115 ]

def f (C, k) :
    return 0.00009676 * k/4 * C + 15.16 * k /4

def g (C, k) :
    return 0.0001640 * k * C + 24.71 * k


write_1 = [x/div for x in write_1]
# write_2 = [x/div for x in write_2]
write_4 = [x/div for x in write_4]
write_1.reverse()
write_4.reverse()

plt.xscale("log")
plt.plot(num_accesses, g(num_accesses, 1), color = "blue", label = "W(C,1)", linestyle = "-")
plt.plot(num_accesses, g(num_accesses, 2), color = "orange", label = "W(C,2)", linestyle = "-")
plt.plot(num_accesses, g(num_accesses, 4), color = "purple", label = "W(C,4)", linestyle = "-")


plt.plot(num_accesses, write_1, color = "blue", label = "1 thread", linestyle="--", marker="o")
# plt.plot(num_accesses, write_2, color = "orange", label = "2 threads", linestyle="-", marker="o")
plt.plot(num_accesses, write_4, color = "purple", label = "4 threads", linestyle="--", marker="o")

plt.legend()
plt.ylabel('Time to Write 10 GiB / Thread (sec)')
plt.xlabel('Number of Chunks Written')
plt.title('Sequential vs. Random Writes')
plt.show()
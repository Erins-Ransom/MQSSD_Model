#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

div = 1000000
X = np.array([4, 8, 16, 32, 64, 128, 256, 512, 1024])

full_cost_accesses = np.array([10 * 1024 * 1024 / x for x in X])

read_1 = [ 262596525,151394703,86129980,44621327,31051442,22164434,17554204,14335611,12937439 ]
read_2 = [ 262017254,149418763,88431134,53611844,30427763,19561153,14332270,13062896,10491011 ]
read_4 = [ 268567972,152792825,91411930,55986412,34687566,22902319,17401157,14659561,13640401]
read_8 = [ 229224217,134899662,84940648,56310676,39986670,30777319,26705371,25848251,26174329 ]
read_16 = [ 289051481,167247826,109621645,79961263,63453789,54729990,52745520,51542956,52257972 ]
read_32 = [ 375328136,237254201,170278875,137390324,123581470,109628950,105224989,103012849,104370086 ]
read_64 = [ 667919433,420740733,314820805,274258004,247983681,219718904,211240460,207393897,210266665 ]

write_1 = [ 436602397,283747339,117798463,76703769,52341773,37885014,28017720,26049917,21815967 ]
write_2 = [ ]
write_4 = [ 1679058391,1027773281,560814878,323728925,223598178,193814229,156318514,137191191,118361115 ]

def f (C, k) :
    return 0.00009676 * k/4 * C + 15.16 * k /4

def g (C, k) :
    return 0.0001640 * k * C + 24.71 * k

read_1 = [x/div for x in read_1]
read_2 = [x/div for x in read_2]
read_4 = [x/div for x in read_4]
read_8 = [x/div for x in read_8]
read_16 = [x/div for x in read_16]
read_32 = [x/div for x in read_32]
read_64 = [x/div for x in read_64]

write_1 = [x/div for x in write_1]
write_2 = [x/div for x in write_2]
write_4 = [x/div for x in write_4]

plt.xscale("log")
plt.plot(X, read_1, label = "read 1 thread", linestyle="--", marker="x")
# plt.plot(X, read_2, label = "read 2 threads", linestyle="--", marker="x")
plt.plot(X, read_4, label = "read 4 threads", linestyle="--", marker="x")

plt.plot(X, f(full_cost_accesses, 4), label = "R(C,4)", linestyle = "-")
# plt.plot(X, f(full_cost_accesses, 16), label = "R(C,16)", linestyle = "-")
# plt.plot(X, f(full_cost_accesses, 64), label = "R(C,64)", linestyle = "-")

plt.plot(X, g(full_cost_accesses, 1), label = "W(C,1)", linestyle = "-")
plt.plot(X, g(full_cost_accesses, 4), label = "W(C,4)", linestyle = "-")

# plt.plot(X, read_8, label = "read 8 threads", linestyle="--", marker="x")
plt.plot(X, read_16, label = "read 16 threads", linestyle="--", marker="x")
# plt.plot(X, read_32, label = "read 32 threads", linestyle="--", marker="x")
# plt.plot(X, read_64, label = "read 64 threads", linestyle="--", marker="x")

plt.plot(X, write_1, label = "write 1 thread", linestyle="--", marker="o")
# plt.plot(X, write_2, label = "write 2 threads", linestyle="-", marker="o")
plt.plot(X, write_4, label = "write 4 threads", linestyle="--", marker="o")

plt.legend()
plt.ylabel('Time to Read 10 GiB / Thread (sec)')
plt.xlabel('Size of Random Reads/Writes (KiB)')
plt.title('Sequential vs. Random Access')
plt.show()
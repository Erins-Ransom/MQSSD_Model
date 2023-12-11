#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import math

div = 1000000
X = np.array([4, 8, 16, 32, 64, 128, 256, 512, 1024])

rand_accesses = np.array([10 * 1024 * 1024 / x for x in X])

data = [[ 262596525,151394703,86129980,44621327,31051442,22164434,17554204,14335611,12937439 ], 
        [ 262017254,149418763,88431134,53611844,30427763,19561153,14332270,13062896,10491011 ], 
        [ 241500778,138735371,83845543,52047312,33375451,21473750,16767549,14293060,13392772 ], 
        [ 229224217,134899662,84940648,56310676,39986670,30777319,26705371,25848251,26174329 ], 
        [ 289051481,167247826,109621645,79961263,63453789,54729990,52745520,51542956,52257972 ], 
        [ 375328136,237254201,170278875,137390324,123581470,109628950,105224989,103012849,104370086 ], 
        [ 667919433,420740733,314820805,274258004,247983681,219718904,211240460,207393897,210266665 ]]


def f_4 (C, k) :
    return 0.00008782 * k/4 * C + 17.16 * k/4

def f_8 (C, k) :
    return 0.00003938 * k/4 * C + 13.485 * k/4

def f_16 (C, k): 
    return 0.00002281 * k/4 * C + 12.311 * k/4

def f_32 (C, k) :
    return 0.00001299 * k/4 * C + 12.813 * k/4

def f_64 (C, k):
    return 0.00001082 * k/4 * C + 12.975 * k/4


def t (k) :
    return 0.0000027 + 0.000085 * 4 / k

def a (k) :
    return 11.845 + 4.8295 * 4 / k

def h (C, k) :
    return t (k) * k/4 * C + 12.813 * k/4



to_plot = [ [ x/div for x in line ] for line in data ]



plt.xscale("log")
# plt.plot(rand_accesses, to_plot[0], color = "blue", label = "read 1 thread", linestyle=" ", marker="o")
# plt.plot(rand_accesses, to_plot[1], color = "blue", label = "read 2 threads", linestyle=" ", marker="o")
plt.plot(rand_accesses, to_plot[2], color = "blue", label = "4 threads", linestyle=" ", marker="o")
plt.plot(rand_accesses, to_plot[3], color = "orange", label = "8 threads", linestyle=" ", marker="o")
plt.plot(rand_accesses, to_plot[4], color = "purple", label = "16 threads", linestyle=" ", marker="o")
plt.plot(rand_accesses, to_plot[5], color = "red", label = "32 threads", linestyle=" ", marker="o")
plt.plot(rand_accesses, to_plot[6], color = "gold", label = "64 threads", linestyle=" ", marker="o")

# plt.plot(rand_accesses, f_4(rand_accesses, 4), color = "blue", label = "a = 6.5, t = 87.8 usec", linestyle = "-")
# plt.plot(rand_accesses, f_8(rand_accesses, 8), color = "orange", label = "a = 5.1, t = 39.3 usec", linestyle = "-")
# plt.plot(rand_accesses, f_16(rand_accesses, 16), color = "purple", label = "a = 4.7, t = 22.8 usec", linestyle = "-")
# plt.plot(rand_accesses, f_32(rand_accesses, 32), color = "red", label = "a = 4.9, t = 13.0 usec", linestyle = "-")
# plt.plot(rand_accesses, f_64(rand_accesses, 64), color = "gold", label = "a = 4.9, t = 10.8 usec", linestyle = "-")


plt.plot(rand_accesses, h(rand_accesses, 4), color = "blue", label = "R(r,4)", linestyle = "-")
plt.plot(rand_accesses, h(rand_accesses, 8), color = "orange", label = "R(r,8)", linestyle = "-")
plt.plot(rand_accesses, h(rand_accesses, 16), color = "purple", label = "R(r,16)", linestyle = "-")
plt.plot(rand_accesses, h(rand_accesses, 32), color = "red", label = "R(r,32)", linestyle = "-")
plt.plot(rand_accesses, h(rand_accesses, 64), color = "gold", label = "R(r,64)", linestyle = "-")




plt.legend()
plt.ylabel('Time to Read 10 GiB / Thread (sec)')
plt.xlabel('Number of Random Accesses')
plt.title('Sequential vs. Random Reads')
plt.show()
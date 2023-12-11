#!/usr/bin/env python3
import matplotlib.pyplot as plt

div = 1000000
X = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024 ]

data = [[ 1221893,1255109,1425698,2341854,3135212,3682565,4289196,5149214,6901756,10075717,16402519 ], 
        [ 1517401,1533887,1619931,2593903,3185458,3763273,4149484,4696143,5700412,7278630,9956290 ], 
        [ 2333576,2408991,3884454,4131537,4336583,4549140,4755288,5192335,5531163,6396251,7810427 ],
        [ 7447985,8229933,8214634,8446518,8746083,8830761,8912066,8918228,9170515,9568743,10156639 ], 
        [ 16516213,16484813,16580657,17087529,17700831,17785859,17736534,17870622,17992426,18200361,18555946 ], 
        [ 33076835,33117358,33256588,34060742,35410564,35545304,35539845,35582292,35666737,35878374,36138770 ],
        [ 66408051,66269650,66584041,68350983,71014788,71333764,71253832,71187797,71511871,71435395,473711066 ]]

to_plot = [ [ x/div for x in line ] for line in data ]

def t (k) :
    k = max(k, 4)
    return 0.0000027 + 0.000085 * 4 / k

def R (f, k) :
    f = max(f,4)
    return k * 10 * 1024 * 1024 * ((0.0000009091 * 128/f) + (t(k) + 0.0000094) * (1 - 128/f)) / 4 


# plt.xscale("log")


# plt.plot(X, [R(x,1) for x in X], label = "R(f,1)", color = "blue", linestyle="-")
# plt.plot(X, [R(x,2) for x in X], label = "R(f,2)", color = "orange", linestyle="-")
# plt.plot(X, [R(x,4) for x in X], label = "R(f,4)", color = "purple", linestyle="-")
# plt.plot(X, [R(x,8) for x in X], label = "R(f,8)", color = "gold", linestyle="-")

y = 4
z = 11
# plt.plot(X[y:z], to_plot[0][y:z], label = "1 thread", color = "blue", linestyle=" ", marker="o")
# plt.plot(X[y:z], to_plot[1][y:z], label = "2 threads", color = "orange", linestyle=" ", marker="o")
plt.plot(X[y:z], to_plot[2][y:z], label = "4 threads", color = "blue", linestyle=" ", marker="o")
plt.plot(X[y:z], to_plot[3][y:z], label = "8 threads", color = "orange", linestyle=" ", marker="o")
plt.plot(X[y:z], to_plot[4][y:z], label = "16 threads", color = "purple", linestyle=" ", marker="o")
plt.plot(X[y:z], to_plot[5][y:z], label = "32 threads", color = "red", linestyle=" ", marker="o")
# plt.plot(X[y:z], to_plot[6][y:z], label = "64 threads", color = "gold", linestyle=" ", marker="o")


plt.legend()
plt.ylabel('Time to Read/Write 10 GiB (sec)')
plt.xlabel('Working Set Size (MiB)')
plt.title('Working Set Size')
plt.show()
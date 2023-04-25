#!/usr/bin/env python3
import matplotlib.pyplot as plt

div = 1000000
X = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024 ]

read = [ 1211167,1249277,1415169,2266819,2878579,3475015,3900280,4557277,5893542,8265029 ]
write= [ 2333909,2400728,2535071,2949662,3686764,4979255,5976841,7098203,9199453,14991572 ]

read_4 = [ 2318690,2348130,2490397,4014285,4424199,4612937,4799806,5219148,5694158,7230739 ] 
write_4 = [ 10516185,13485366,12732924,13381814,15467176,17471936,18981823,20531423,23354193,34611853 ]

read = [x/div for x in read]
write = [x/div for x in write]
read_4 = [x/div for x in read_4]
write_4 = [x/div for x in write_4]


# plt.xscale("log")
plt.plot(X, read, label = "read", linestyle="--", marker="o")
plt.plot(X, write, label = "write", linestyle="--", marker="o")
plt.plot(X, read_4, label = "read (4 threads)", linestyle="--", marker="o")
plt.plot(X, write_4, label = "write (4 threads)", linestyle="--", marker="o")
plt.legend()
plt.ylabel('Time to Read/Write 10 GiB (sec)')
plt.xlabel('Working Set Size (MiB)')
plt.title('Working Set Size')
plt.show()
#!/usr/bin/env python3
import matplotlib.pyplot as plt

div = 1000000
X = [1, 2, 4, 8, 16, 32, 64]

read = [ 11742436,9937401,13921738,26391614,52477230,104959980,211616344 ]
write= [ 10710387,42516338,107948256,232857656,467128810,951848755,1939831293 ]

read = [x/div for x in read]
write = [x/div for x in write]

plt.xscale("log")
plt.plot(X, read, label = "read", linestyle="--", marker="o")
plt.plot(X, write, label = "write", linestyle="--", marker="o")
plt.legend()
plt.ylabel('Time to Read/Write 10 GiB / Thread (sec)')
plt.xlabel('Number of Threads')
plt.title('Parallelism for Sequential Access')
plt.show()
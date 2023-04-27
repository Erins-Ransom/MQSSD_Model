#!/usr/bin/env python3
import matplotlib.pyplot as plt

div = 1000000
X = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024 ]

# read = [ 1211167,1249277,1415169,2266819,2878579,3475015,3900280,4557277,5893542,8265029 ]
# write= [ 2333909,2400728,2535071,2949662,3686764,4979255,5976841,7098203,9199453,14991572 ]

# read_4 = [ 2318690,2348130,2490397,4014285,4424199,4612937,4799806,5219148,5694158,7230739 ] 
# write_4 = [ 10516185,13485366,12732924,13381814,15467176,17471936,18981823,20531423,23354193,34611853 ]

data = [[ 2383320,2423581,2554996,3040902,4006278,5220205,6005990,7133514,9241158,14990402,25287285 ], 
        [ 5231349,5280411,5208048,5634650,6767124,7916367,8458867,9899874,12478775,21352676,43374321 ], 
        [ 11246493,12674631,12696095,13647539,16120042,17814668,20079933,21909582,24477282,36161158,84862093 ],
        [ 27160338,29943321,29439905,30979351,35292952,39938319,41706181,44892403,48779693,67673473,163830674 ]]

to_plot = [ [ x/div for x in line ] for line in data ]

def W (f, k) :
    f = max(f,128)
    return k * 10 * 1024 * 1024 * ((0.0000009091 * 128/f) + (0.0001640 + 0.0000094) * (1 - 128/f)) / 4 


# plt.xscale("log")


# plt.plot(X, [W(x,1) for x in X], label = "W(f,1)", color = "blue", linestyle="-")
# plt.plot(X, [W(x,2) for x in X], label = "W(f,2)", color = "orange", linestyle="-")
# plt.plot(X, [W(x,4) for x in X], label = "W(f,4)", color = "purple", linestyle="-")
# plt.plot(X, [W(x,8) for x in X], label = "W(f,8)", color = "gold", linestyle="-")


plt.plot(X, to_plot[0], label = "1 thread", color = "blue", linestyle=" ", marker="o")
plt.plot(X, to_plot[1], label = "2 threads", color = "orange", linestyle=" ", marker="o")
plt.plot(X, to_plot[2], label = "4 threads", color = "purple", linestyle=" ", marker="o")
plt.plot(X, to_plot[3], label = "8 threads", color = "gold", linestyle=" ", marker="o")


plt.legend()
plt.ylabel('Time to Read/Write 10 GiB (sec)')
plt.xlabel('Working Set Size (MiB)')
plt.title('Working Set Size')
plt.show()
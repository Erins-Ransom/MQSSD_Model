import matplotlib.pyplot as plt
import numpy as np
from baryrat import aaa
import os


B = 512
P = 8
I = int(np.log2(P))
I_max = 8
thread_counts = np.array([2**i for i in range(0, I_max)], dtype=np.float64)
# P = { "gen_5" : 8, "gen_4" : 8, "gen_3" : 4 }

pages_read = 10 * 1024 * 1024 * 1024 / B
acc_size = [ 2 ** i for i in range(9, 21)]
rand_accs = np.array([ pages_read / size for size in acc_size ], dtype=np.float64)

#  colors = ["darkgoldenrod", "darkorchid", "cornflowerblue", "gold", "tan", "violet", "mediumpurple", "goldenrod"]
colors = ["lightskyblue", "orchid", "burlywood", "pink", "gold", "deepskyblue", "darkorchid", "darkgoldenrod"]

data = {}
models = {}



def load_data():
    for dev in ["gen_5", "gen_4", "gen_3"]:
        for op in ["_write", "_read"]:
            path = "../results/" + dev + "/" + op + "/"
            files = os.listdir(path)
            data[dev + op] = np.zeros((I_max, len(rand_accs)), dtype=np.float64)
            for file in files:
                data[dev + op] += np.array([[ float(x) for x in line.split(",") ] for line in open(path + file).read().split()[0:I_max] ], dtype=np.float64) / len(files)


def print_data():
    print("Thread Count : Data")
    for op in ["_write", "_read"]:
        print(op)
        for dev in ["gen_5", "gen_4", "gen_3"]:
            print(dev)
            for i in range(0, 8):
                print("{} : {}".format(2**i, str(data[dev + op][i])))
        


def fit_data():
    m = []
    for dev in ["gen_5", "gen_4", "gen_3"]:
        for op in ["_write", "_read"]:
            m = []
            b = []
            models[dev + op] = []
            for i in range(0, I_max):
                A = np.vstack([rand_accs, np.ones(len(rand_accs), dtype=np.float64)]).T
                models[dev + op].append(np.linalg.lstsq(A, data[dev + op][i] / (2**i), rcond=None)[0])
                m.append(models[dev + op][i][0])
                b.append(models[dev + op][i][1])

            models[dev + op + "_k"] = (aaa(thread_counts, np.array(m, dtype=np.float64)), aaa(thread_counts, np.array(b, dtype=np.float64)))

        

def print_models():
    for op in ["_write", "_read"]:
        print(op)
        for dev in ["gen_5", "gen_4", "gen_3"]:
            print(dev)
            print(models[dev + op + "_k"])
            for i in range(0, I_max):
                print(models[dev + op][i])




def plot_model_params():
    fig, plots = plt.subplots(4,3)
    col_index = {"gen_5" : 0, "gen_4" : 1, "gen_3" : 2}
    row_index = {"_write_m" : 0, "_write_b" : 1, "_read_m" : 2, "_read_b" : 3}
    cost = {"_write_m" : "s", "_write_b" : "B", "_read_m" : "t", "_read_b" : "a"}
    model_index = {"_m" : 0, "_b" : 1}
    for dev in ["gen_5", "gen_4", "gen_3"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            for param in ["_m", "_b"]:
                row = row_index[op + param]
                j = model_index[param]

                vals = np.array([models[dev + op][i][j] for i in range(0, I_max)], dtype=np.float64)
                fit = models[dev + op + "_k"][j](thread_counts)
                if param == "_b":
                    vals /= pages_read
                    fit /= pages_read

                plots[row, col].plot(thread_counts, vals, linestyle=" ", marker="o", color=colors[j + 5 * (row // 2)])
                plots[row, col].set(xlabel="Thread Count", ylabel=cost[op + param] + " (usec)")
                plots[row, col].plot(thread_counts, fit, color=colors[j + 5 * (row // 2)])
            
    for plot in plots.flat:
        plot.label_outer()

    fig.suptitle('Model Parameters by Thread Count')
    plt.show()


def plot_per_thread_models():
    fig, plots = plt.subplots(2,3)
    col_index = {"gen_5" : 0, "gen_4" : 1, "gen_3" : 2}
    row_index = {"_write" : 0, "_read" : 1}
    band_cost = {"_write" : "B", "_read" : "a"}
    setup_cost = {"_write" : "s", "_read" : "t"}
    for dev in ["gen_5", "gen_4", "gen_3"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            row = row_index[op]
            for i in range(0, I_max):
                plots[row, col].plot(rand_accs, data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i])
                plots[row, col].plot(rand_accs, (rand_accs * models[dev + op][i][0] + models[dev + op][i][1]) * (2**i) / 1000000, color=colors[i], 
                                     label="k={}, {}={}, {}={} usec".format(2**i, setup_cost[op], round(models[dev + op][i][0], 1), band_cost[op], round(models[dev + op][i][1] / pages_read, 2)))
                plots[row, col].set(xlabel="Number of Random Accesses", ylabel="Total Latency (sec)", xscale="log")
            plots[row, col].legend()

    for plot in plots.flat:
        plot.label_outer()

    fig.suptitle('Latency by Number of Random Accesses')
    plt.show()


def cost_function(dev, op, num_rand_accs, num_threads):
    return (models[dev + op + "_k"][0](num_threads) * num_rand_accs + models[dev + op + "_k"][1](num_threads)) * num_threads / 1000000
  

def plot_by_random_accesses():
    fig, plots = plt.subplots(2,3)
    col_index = {"gen_5" : 0, "gen_4" : 1, "gen_3" : 2}
    row_index = {"_write" : 0, "_read" : 1}
    cost_type = {"_write" : "W", "_read" : "R"}
    for dev in ["gen_5", "gen_4", "gen_3"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            row = row_index[op]
            for i in range(0, I_max):
                plots[row, col].plot(rand_accs, data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i])
                plots[row, col].plot(rand_accs, cost_function(dev, op, rand_accs, (2**i)), color=colors[i], label="{}(r, {})".format(cost_type[op], (2**i)))
                plots[row, col].set(xlabel="Number of Random Accesses", ylabel="Total Latency (sec)", xscale="log")
            plots[row, col].legend()

    for plot in plots.flat:
        plot.label_outer()

    fig.suptitle('Latency by Number of Random Accesses')
    plt.show()


def plot_writes_by_access_size():
    fig, plots = plt.subplots(1,3)
    op = "_write"
    plots_index = 0
    for dev in ["gen_5", "gen_4", "gen_3"]:    
        for i in range(0, I_max):
            plots[plots_index].plot(rand_accs, cost_function(dev, op, rand_accs, (2**i)), color=colors[i], label = "W(r,{})".format(2**i), linestyle = "-")
            plots[plots_index].plot(rand_accs, data[dev + op][i] / 1000000, label ="{} threads".format(2**i),  color=colors[i], linestyle=" ", marker="o")
        plots[plots_index].set(xlabel="Number of Random Pages Read", ylabel="Time to Write 10 GiB / Thread (sec)", xscale="log")
        plots[plots_index].set_title(dev)
        plots_index += 1

    for plot in plots:
        plot.label_outer()
        plot.legend()

    fig.suptitle('Write Latency by Access Size')
    plt.show()







# def fit_data(X, Y):

#     m = ((X - X.mean()) * (Y - Y.mean())).sum() / ((X - X.mean()) * (X - X.mean())).sum()
#     b = Y.mean() - m * X.mean()

#     return m, b

# def train_models():
#     for dev in ["gen_5"]: #, "gen_4", "gen_3"]:
#         # for op in ["_write", "_read"]:
#         for op in ["_read"]:
#             models[dev + op] = LinearRegression()
#             models[dev + op].fit(rand_accs, data[dev + op][0] )
#             # models[dev + op + "_k"] = LinearRegression()
#             # models[dev + op + "_k"].fit()
        



load_data()
# print_data()
fit_data()
print_models()





# plot_model_params()
# plot_per_thread_models()
# plot_writes_by_access_size()
plot_by_random_accesses()

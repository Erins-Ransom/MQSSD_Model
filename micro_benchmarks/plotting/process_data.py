import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from baryrat import aaa
import os


B = 512
P = 16
I = int(np.log2(P))
I_max = 8
thread_counts = np.array([2**i for i in range(0, I_max)], dtype=np.float64)
# P = { "Crucial" : 8, "Samsung" : 8, "PNY" : 4 }

pages_per_thread = 10 * 1024 * 1024 * 1024 / B
acc_size = [ 2 ** i for i in range(9, 21)]
rand_accs = np.array([ pages_per_thread / size for size in acc_size ], dtype=np.float64)

#  colors = ["darkgoldenrod", "darkorchid", "cornflowerblue", "gold", "tan", "violet", "mediumpurple", "goldenrod"]
# colors = ["lightskyblue", "orchid", "burlywood", "pink", "gold", "deepskyblue", "darkorchid", "darkgoldenrod"]
colors = ["lightcoral", "chocolate", "tan", "gold", "yellowgreen", "skyblue", "mediumpurple", "orchid"]

data = {}
mean_data = {}
models = {}
R_squares = {}



#############################################################
#                   Data Processing                         #
#############################################################

def load_data():
    for dev in ["Crucial", "Samsung", "PNY"]:
        for op in ["_write", "_read"]:
            path = "../results/" + dev + "/" + op + "/"
            files = os.listdir(path)
            mean_data[dev + op] = np.zeros((I_max, len(rand_accs)), dtype=np.float64)
            temp = []
            for file in files:
                temp.append(np.array([[ float(x) for x in line.split(",") ] for line in open(path + file).read().split()[0:I_max] ], dtype=np.float64))
                mean_data[dev + op] += temp[-1] / len(files)

            print(dev + op)
            data[dev + op] = np.array([[[ exp[i][j] for exp in temp] for j in range(len(rand_accs))] for i in range(I_max)], dtype=np.float64)


def print_data():
    print("Thread Count : Data")
    for op in ["_write", "_read"]:
        print(op)
        for dev in ["Crucial", "Samsung", "PNY"]:
            print(dev)
            print(data[dev + op])
            print(np.var(data[dev + op], axis=2))
            for i in range(0, I_max):
                print("{} : {}".format(2**i, str(mean_data[dev + op][i])))
        


def test_0(x, c0, c1):
    return c0 / x + c1

def test_1(x, c0, c1, c2):
    return c0 / x + c1 * x + c2


def fit_data(): 
    m = [] 
    for dev in ["Crucial", "Samsung", "PNY"]: 
        for op in ["_write", "_read"]: 
            m = [] 
            b = [] 
            models[dev + op] = [] 
            R_squares[dev + op] = []
            for i in range(0, I_max): 
                y = mean_data[dev + op][i] / (2**i)
                A = np.vstack([rand_accs, np.ones(len(rand_accs), dtype=np.float64)]).T 
                fit = np.linalg.lstsq(A, y, rcond=None)
                R_squares[dev + op].append(1 - fit[1] / sum((y - y.mean())**2))
                models[dev + op].append(fit[0])
                m.append(models[dev + op][i][0])
                b.append(models[dev + op][i][1])

            models[dev + op + "_k"] = (aaa(thread_counts, np.array(m, dtype=np.float64)), aaa(thread_counts, np.array(b, dtype=np.float64)))

        

def print_models():
    for op in ["_write", "_read"]:
        print(op)
        for dev in ["Crucial", "Samsung", "PNY"]:
            print(dev)
            print(models[dev + op + "_k"])
            for i in range(0, I_max):
                print(models[dev + op][i], "bandwith cost = {} usec, R^2 = {}".format(models[dev + op][i][1] / pages_per_thread, R_squares[dev + op][i]))




def plot_model_params():
    fig, plots = plt.subplots(4,3)
    col_index = {"Crucial" : 0, "Samsung" : 1, "PNY" : 2}
    row_index = {"_write_m" : 0, "_write_b" : 1, "_read_m" : 2, "_read_b" : 3}
    cost = {"_write_m" : "s(k)", "_write_b" : "B(k)", "_read_m" : "t(k)", "_read_b" : "a(k)"}
    model_index = {"_m" : 0, "_b" : 1}
    for dev in ["Crucial", "Samsung", "PNY"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            for param in ["_m", "_b"]:
                row = row_index[op + param]
                j = model_index[param]

                vals = np.array([models[dev + op][i][j] for i in range(0, I_max)], dtype=np.float64)
                fit = models[dev + op + "_k"][j](thread_counts)
                if param == "_b":
                    vals /= pages_per_thread
                    fit /= pages_per_thread

                plots[row, col].plot(thread_counts, vals, linestyle=" ", marker="o", color=colors[j + 5 * (row // 2)])
                plots[row, col].set(xlabel="Thread Count", ylabel=cost[op + param] + " (usec)")
                plots[row, col].plot(thread_counts, fit, color=colors[j + 5 * (row // 2)])
            
    for plot in plots.flat:
        plot.label_outer()

    # fig.suptitle('Model Parameters by Thread Count')
    fig.tight_layout()
    plt.show()


def plot_per_thread_models():
    fig, plots = plt.subplots(2,3)
    col_index = {"Crucial" : 0, "Samsung" : 1, "PNY" : 2}
    row_index = {"_write" : 0, "_read" : 1}
    band_cost = {"_write" : "B", "_read" : "a"}
    setup_cost = {"_write" : "s", "_read" : "t"}
    for dev in ["Crucial", "Samsung", "PNY"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            row = row_index[op]
            for i in range(0, I_max):
                plots[row, col].plot(rand_accs, mean_data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i])
                plots[row, col].plot(rand_accs, (rand_accs * models[dev + op][i][0] + models[dev + op][i][1]) * (2**i) / 1000000, color=colors[i], 
                                     label="k={}, {}={}, {}={} usec".format(2**i, setup_cost[op], round(models[dev + op][i][0], 1), band_cost[op], round(models[dev + op][i][1] / pages_per_thread, 2)))
                plots[row, col].set(xlabel="Number of Random Accesses", ylabel="Total Latency (sec)", xscale="log")
            plots[row, col].legend()

    for plot in plots.flat:
        plot.label_outer()

    fig.suptitle('Latency by Number of Random Accesses')
    plt.show()

#############################################################



#############################################################
#             Micro-Benchmark Cost Functions                #
#############################################################

def cost_function(dev, op, rand_accs_per_thread, num_threads):
    return (models[dev + op + "_k"][0](num_threads) * rand_accs_per_thread + models[dev + op + "_k"][1](num_threads)) * num_threads / 1000000


def DAM_cost(dev, op, rand_accs_per_thread, num_threads):
    unit_cost = models[dev + op][0][1] / pages_per_thread
    return np.ones(len(rand_accs_per_thread), dtype=np.float64) * pages_per_thread * num_threads * unit_cost / 1000000
  

def PDAM_cost(dev, op, rand_accs_per_thread, num_threads):
    unit_cost = models[dev + op][0][1] / pages_per_thread
    if pages_per_thread > P :
        return np.ones(len(rand_accs_per_thread), dtype=np.float64) * pages_per_thread * num_threads * unit_cost / ( P * 1000000 )
    else :
        return np.ones(len(rand_accs_per_thread), dtype=np.float64) * pages_per_thread * unit_cost / 1000000
    

def affine_cost(dev, op, rand_accs_per_thread, num_threads):
    return (models[dev + op][0][0] * rand_accs_per_thread + models[dev + op][0][1]) * num_threads / 1000000


#############################################################



#############################################################
#                   Model Comparisons                       #
#############################################################

def plot_model_comparison(dev):
    col_index = {DAM_cost : 0, PDAM_cost : 1, affine_cost : 2, cost_function : 3}
    col_label = {DAM_cost : "DAM", PDAM_cost : "PDAM", affine_cost : "Affine", cost_function : "MQSSD"}
    row_index = {"_write" : 0, "_read" : 1}
    label_op = {"_write" : "Write", "_read" : "Read"}
    fig, plots = plt.subplots(2, 4)
    y_top = { "_write" : mean_data[dev + "_write"][-2].max() / 1000000 + 50, "_read" : mean_data[dev + "_read"][-2].max() / 1000000 + 10}
    y_bottom = { "_write" : -50, "_read" : -5}
    for cost_model in [DAM_cost, PDAM_cost, affine_cost, cost_function]:
        col = col_index[cost_model]
        plots[0, col].set_title(col_label[cost_model])
        for op in ["_write", "_read"]:
            row = row_index[op]
            for i in range(0, I_max):
                plots[row, col].plot(rand_accs * (2**i), mean_data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i], label="k={}".format(2**i))
                plots[row, col].plot(rand_accs * (2**i), cost_model(dev, op, rand_accs, 2**i), color=colors[i])
            plots[row, col].set(ylabel="Time to {} 10 GiB / Thread (sec)".format(label_op[op]), xlabel="Total Random Accesses", xscale="log")
            plots[row, col].set_ylim(top=y_top[op], bottom=y_bottom[op])


    for plot in plots.flat:
        plot.label_outer()

    # fig.suptitle('Microbenchmark Model Comparison')
    plots[0, 0].legend()
    fig.tight_layout()
    plt.show()




def plot_single_model(dev, cost_model, op):
    label = {DAM_cost : "DAM", PDAM_cost : "PDAM", affine_cost : "Affine", cost_function : "MQSSD", None : None } 
    y_top = { "_write" : mean_data[dev + "_write"].max() / 1000000 + 10, "_read" : mean_data[dev + "_read"].max() / 1000000 + 10}
    y_bottom = { "_write" : -100, "_read" : -5}
    for i in range(0, I_max):
        plt.plot(rand_accs * (2**i), mean_data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i], label="k={}".format(2**i))
        if cost_model != None :
            plt.plot(rand_accs * (2**i), cost_model(dev, op, rand_accs, 2**i), color=colors[i])
    plt.ylabel("Time to {} 10 GiB / Thread (sec)".format(op))
    plt.xlabel("Total Random Accesses")
    plt.xscale("log")
    plt.ylim(top=y_top[op], bottom=y_bottom[op])
    plt.legend()
    if cost_model == None :
        plt.title("Benchmark Results")
    else :
        plt.title("{} Model vs. Benchmark".format(label[cost_model]))
    plt.show()




def plot_by_random_accesses_per_thread():
    fig, plots = plt.subplots(2,3)
    col_index = {"Crucial" : 0, "Samsung" : 1, "PNY" : 2}
    row_index = {"_write" : 0, "_read" : 1}
    cost_type = {"_write" : "W", "_read" : "R"}
    for dev in ["Crucial", "Samsung", "PNY"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            row = row_index[op]
            for i in range(0, I_max):
                plots[row, col].plot(rand_accs, mean_data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i])
                plots[row, col].plot(rand_accs, cost_function(dev, op, rand_accs, (2**i)), color=colors[i], label="{}(r, {})".format(cost_type[op], (2**i)))
                plots[row, col].set(xlabel="Random Accesses Per-Thread", ylabel="Time to {} 10 GiB / Thread (sec)".format(op), xscale="log")
            plots[row, col].legend()

    for plot in plots.flat:
        plot.label_outer()

    fig.suptitle('Latency by Number of Random Accesses Per Thread')
    plt.show()


def plot_by_total_random_accesses():
    fig, plots = plt.subplots(2,3)
    label_op = {"_write" : "Write", "_read" : "Read"}
    col_index = {"Crucial" : 0, "Samsung" : 1, "PNY" : 2}
    row_index = {"_write" : 0, "_read" : 1}
    cost_type = {"_write" : "W", "_read" : "R"}
    for dev in ["Crucial", "Samsung", "PNY"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            row = row_index[op]
            for i in range(0, I_max):
                plots[row, col].plot(rand_accs * (2**i), mean_data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i], label="k={}".format(2**i))
                # plots[row, col].plot(rand_accs * (2**i), data[dev + op][i] / 1000000, linestyle=" ", marker="o", color=colors[i])
                # plots[row, col].plot(rand_accs * (2**i), cost_function(dev, op, rand_accs, (2**i)), color=colors[i], label="{}(r, {})".format(cost_type[op], (2**i)))
                plots[row, col].set(xlabel="Total Random Accesses", ylabel="Time to {} 10 GiB / Thread (sec)".format(label_op[op]), xscale="log")
            

    for plot in plots.flat:
        plot.label_outer()

    # fig.suptitle('Latency by Total Random Accesses & Thread Count')
    plots[0, 0].legend()
    fig.tight_layout()
    plt.show()

#############################################################





#############################################################
#                   LSM-Tree Figures                        #
#############################################################
    


def lookup_cost_by_fannout(dev, N=100 * 1024 * 1024 * 1024):
    
    F_vals = np.array([2,4,6,8,10,12,14,16,18,20], dtype=np.float64) 
        
    def cost(F, tiered):
        if not tiered :
            k = np.log(N/512.0) / np.log(F)
    
        else:
            k = F * np.log(N/512.0) / np.log(F)

        return  k * (models[dev + "_read_k"][0](k) + models[dev + "_read_k"][1](k) / pages_per_thread) / 1000
        
    plt.plot(F_vals, cost(F_vals, False), label="Leveled")
    plt.plot(F_vals, cost(F_vals, True), label="Tiered")
    
    plt.ylabel("Predicted Lookup Latency (ms)")
    plt.xlabel("Growth Factor (F)")
    plt.legend()
    plt.show()





#############################################################







load_data()
print_data()
fit_data()
print_models()





# plot_model_params()
# plot_per_thread_models()
# plot_writes_by_access_size()
# plot_by_random_accesses_per_thread()
# plot_by_total_random_accesses()
# plot_model_comparison("Samsung")
# plot_single_model("Samsung", affine_cost, "_read")
# lookup_cost_by_fannout("Samsung")
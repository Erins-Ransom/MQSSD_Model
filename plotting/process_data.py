import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
# from baryrat import aaa
import os

val_size = 512
num_keys = 10000000
num_queries = 1000000
T = 32 * 1024 * 1024
C = 4
B = 512
B_ = 4 * 1024
P = 16
I = int(np.log2(P))
I_max = 8
thread_counts = np.array([2**i for i in range(0, I_max)], dtype=np.float64)

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
#          S1 - Micro Benchmark Data Processing             #
#############################################################

def load_data(results_path="../micro_benchmarks/results/"):
    for dev in ["Crucial", "Samsung", "PNY"]:
        for op in ["_write", "_read"]:
            path = results_path + dev + "/" + op + "/"
            files = os.listdir(path)
            mean_data[dev + op] = np.zeros((I_max, len(rand_accs)), dtype=np.float64)
            temp = []
            for file in files:
                temp.append(np.array([[ float(x) for x in line.split(",") ] for line in open(path + file).read().split()[0:I_max] ], dtype=np.float64))
                mean_data[dev + op] += temp[-1] / len(files)

            # print(dev + op)
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
        

def fit_rat_n3d3(x, n0, n1, n2, d0, d1, d2):
    return (n0 + n1*x + n2*(x**2)) / (d0 + d1*x + d2*(x**2))


def fit_rat_n4d3(x, n0, n1, n2, n3, d0, d1, d2):
    return (n0 + n1*x + n2*(x**2) + n3*(x**3)) / (d0 + d1*x + d2*(x**2))


def cost(k, dev, op, bandwidth=0):
    """
    Returns a fitted setup or bandwidth cost for the respective device and operation.
    k = <thread_count>
    dev = "Crucial" / "Samsung" / "PNY"
    op = "_read" / "_write
    bandwidth = 0 => setup cost
    bandwidth = 1 => bandwidth cost
    """
    
    c = models[dev + op + "_fit"][bandwidth][0]

    if op == "_write" and  bandwidth == 0 :
        return (c[0] + c[1]*k + c[2]*(k**2) + c[3]*(k**3)) / (c[4] + c[5]*k + c[6]*(k**2))
    else :
        return (c[0] + c[1]*k + c[2]*(k**2)) / (c[3] + c[4]*k + c[5]*(k**2))


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

            if op == "_write":
                models[dev + op + "_fit"] = (curve_fit(fit_rat_n4d3, thread_counts, np.array(m, dtype=np.float64)), curve_fit(fit_rat_n3d3, thread_counts, np.array(b, dtype=np.float64)))
            else :
                models[dev + op + "_fit"] = (curve_fit(fit_rat_n3d3, thread_counts, np.array(m, dtype=np.float64)), curve_fit(fit_rat_n3d3, thread_counts, np.array(b, dtype=np.float64)))

            # models[dev + op + "_k"] = (aaa(thread_counts, np.array(m, dtype=np.float64)), aaa(thread_counts, np.array(b, dtype=np.float64)))
        

def print_models():
    for op in ["_write", "_read"]:
        print(op)
        for dev in ["Crucial", "Samsung", "PNY"]:
            print(dev)
            # print(models[dev + op + "_k"])
            print(models[dev + op + "_fit"])
            for i in range(0, I_max):
                print(models[dev + op][i], "bandwith cost = {} usec, R^2 = {}".format(models[dev + op][i][1] / pages_per_thread, R_squares[dev + op][i]))


def plot_model_params():
    fig, plots = plt.subplots(4,3)
    col_index = {"Crucial" : 0, "Samsung" : 1, "PNY" : 2}
    row_index = {"_write_m" : 0, "_write_b" : 1, "_read_m" : 2, "_read_b" : 3}
    cost_label = {"_write_m" : "s(k)", "_write_b" : "B(k)", "_read_m" : "t(k)", "_read_b" : "a(k)"}
    model_index = {"_m" : 0, "_b" : 1}
    for dev in ["Crucial", "Samsung", "PNY"]:
        col = col_index[dev]
        plots[0, col].set_title(dev)
        for op in ["_write", "_read"]:
            for param in ["_m", "_b"]:
                row = row_index[op + param]
                j = model_index[param]

                vals = np.array([models[dev + op][i][j] for i in range(0, I_max)], dtype=np.float64)
                # fit = models[dev + op + "_k"][j](thread_counts)
                fit = cost(thread_counts, dev, op, bandwidth=j)
                if param == "_b":
                    vals /= pages_per_thread
                    fit /= pages_per_thread

                plots[row, col].plot(thread_counts, vals, linestyle=" ", marker="o", color=colors[j + 5 * (row // 2)])
                plots[row, col].set(xlabel="Thread Count", ylabel=cost_label[op + param] + " (usec)")
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

####################################################### END-1



#############################################################
#         S2 -  Micro-Benchmark Cost Functions              #
#############################################################

def MQSSD_cost(dev, op, rand_accs_per_thread, num_threads):
    # return (models[dev + op + "_k"][0](num_threads) * rand_accs_per_thread + models[dev + op + "_k"][1](num_threads)) * num_threads / 1000000
    return (cost(num_threads, dev, op) * rand_accs_per_thread + cost(num_threads, dev, op, bandwidth=1)) * num_threads / 1000000


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

####################################################### END-2



#############################################################
#                S3 - Model Comparisons                     #
#############################################################

def plot_model_comparison(dev):
    col_index = {DAM_cost : 0, PDAM_cost : 1, affine_cost : 2, MQSSD_cost : 3}
    col_label = {DAM_cost : "DAM", PDAM_cost : "PDAM", affine_cost : "Affine", MQSSD_cost : "MQSSD"}
    row_index = {"_write" : 0, "_read" : 1}
    label_op = {"_write" : "Write", "_read" : "Read"}
    fig, plots = plt.subplots(2, 4)
    y_top = { "_write" : mean_data[dev + "_write"][-2].max() / 1000000 + 50, "_read" : mean_data[dev + "_read"][-2].max() / 1000000 + 10}
    y_bottom = { "_write" : -50, "_read" : -5}
    for cost_model in [DAM_cost, PDAM_cost, affine_cost, MQSSD_cost]:
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
    label = {DAM_cost : "DAM", PDAM_cost : "PDAM", affine_cost : "Affine", MQSSD_cost : "MQSSD", None : None } 
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
                plots[row, col].plot(rand_accs, MQSSD_cost(dev, op, rand_accs, (2**i)), color=colors[i], label="{}(r, {})".format(cost_type[op], (2**i)))
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
                # plots[row, col].plot(rand_accs * (2**i), MQSSD_cost(dev, op, rand_accs, (2**i)), color=colors[i], label="{}(r, {})".format(cost_type[op], (2**i)))
                plots[row, col].set(xlabel="Total Random Accesses", ylabel="Time to {} 10 GiB / Thread (sec)".format(label_op[op]), xscale="log")
            

    for plot in plots.flat:
        plot.label_outer()

    # fig.suptitle('Latency by Total Random Accesses & Thread Count')
    plots[0, 0].legend()
    fig.tight_layout()
    plt.show()

####################################################### END-3





#############################################################
#             S4 - LSM-Tree Data & Figures                  #
#############################################################

trial_counts = {}
rocksdb_data = {}

file_size = np.array([32, 64, 128], dtype=np.float64)
threads = np.array([2, 4, 8, 16, 32], dtype=np.float64)
fanout = np.array([2, 4, 8, 16], dtype=np.float64)

def gen_rocksdb_csv(out="rocksdb_results.csv", results_path="../rocksdb_exp/results/"):
    vals = {"Batch Code:" : "", "Number of Keys:" : "", "Number of Queries:" : "", "Target File Size:" : "", "Compaction Style:" : "", "Compaction Threads:" : "", "Fanout:" : "", "Dynamic Level:" : "", "RUNTIME of Write Workload:" : "", "RUNTIME of Read Workload:" : ""}
    header = ["Batch Code:", "Compaction Style:", "Dynamic Level:", "Number of Keys:", "Number of Queries:", "Target File Size:", "Compaction Threads:", "Fanout:"]
    times = ["RUNTIME of Write Workload:", "RUNTIME of Read Workload:"]
    csv = open(out, "w")
    for val in header:
        csv.write(val[0:-1] + ",")
    csv.write(times[0][0:-1] + ",")
    csv.write(times[1][0:-1] + "\n")

    for exp in os.listdir(results_path):
        input = open(results_path + "/" + exp + "/exp.txt", "r")
        lines = input.readlines()
        for line in lines[0:10]:
            if line == "\n":
                break
            for val in header:
                if line.startswith(val):
                    if val == "Compaction Threads:":
                        vals[val] = int(line[len(val):].split()[0]) + 1
                    else :
                        vals[val] = line[len(val):].split()[0]

        for line in lines[10:]:
            if line.startswith("RUNTIME"):
                for val in times:
                    if line.startswith(val):
                        vals[val] = line[len(val):].split()[0]
        
        for val in header:
            csv.write("{},".format(vals[val]))
        csv.write("{},".format(vals[times[0]]))
        csv.write("{}\n".format(vals[times[1]]))

        input.close()
        for val in vals.keys():
            vals[val] = ""
    
    csv.close()
                    

def load_rocksdb_data(batch_codes=["0000"], print_=True):

    for layout in ["Level", "Universal"] :
        for op in ["_read", "_write"] :
            trial_counts[layout + op] = np.zeros((len(file_size), len(threads), len(fanout)), dtype=np.int64)
            rocksdb_data[layout + op] = np.zeros((len(file_size), len(threads), len(fanout)), dtype=np.float64)

    for line in open("rocksdb_results.csv", "r").readlines() :
        val = line.split(",")
        if not val[0] in batch_codes :
            continue
        elif not (int(val[3]) == num_keys and int(val[4]) == num_queries) :
            continue
        
        skip = False
        for x in val[5:9] :
            if x == "" :
                print("Bad Line: " + line)

                skip = True
                break
        
        if skip :
            continue
                
        
        i = int(np.log2(int(val[5])/32))
        j = int(np.log2(int(val[6]))) - 1
        k = int(np.log2(int(val[7]))) - 1
        trial_counts[val[1] + "_write"][i][j][k] += 1   
        count = trial_counts[val[1] + "_write"][i][j][k]
        if j == 0 :
            trial_counts[val[1] + "_read"][i][j][k] += 1

        if count > 1 :
            rocksdb_data[val[1] + "_write"][i][j][k] = rocksdb_data[val[1] + "_write"][i][j][k] * (count - 1) / count + float(val[8]) / count
            if j == 0 :
                rocksdb_data[val[1] + "_read"][i][j][k] = rocksdb_data[val[1] + "_read"][i][j][k] * (count - 1) / count + float(val[9]) / count
        else :
            rocksdb_data[val[1] + "_write"][i][j][k] = float(val[8])
            if j == 0 :
                rocksdb_data[val[1] + "_read"][i][j][k] = float(val[9])

    if print_:
        print_rocksdb_data()


def print_rocksdb_data():
    print("Latency (msec) for T,k,F: rocksdb_data[log2(T/32)][log2(k)][log2(F)-1]")
    for layout in ["Level", "Universal"]: 
        for op in ["_write", "_read"]: 
            print(layout + op)
            print("times:")
            print(rocksdb_data[layout + op])
            print("trial counts:")
            print(trial_counts[layout + op])


def comp_cost_by_fanout(dev, layout):
    N = num_keys * val_size
    exp_fanouts = np.array([2, 4, 8, 16], dtype=np.float64)
    fanouts = np.array([x/4 for x in range(8, 64)], dtype=np.float64)
    threads = np.array([2,4,8,16,32], dtype=np.float64)


    def comp_cost(F, k, layout, dev):
        if layout == "Level":
            return N * (np.log(N/(C*T)) / np.log(F)) * F * ((cost(k, dev, "_write", 0) + cost(k, dev, "_read", 0)) / T + (cost(k, dev, "_write", 1) + cost(k, dev, "_read", 1))/B) / 1000000
        elif layout == "Universal":
            return N * (np.log(N/(C*T)) / np.log(F)) * ((cost(k, dev, "_write", 0) + cost(k, dev, "_read", 0)) / T + (cost(k, dev, "_write", 1) + cost(k, dev, "_read", 1))/B) / 1000000

    for i in range(0, len(threads)): 
        # print(comp_cost(fanouts, threads[i], layout, dev))
        plt.plot(fanout, rocksdb_data[layout + "_write"][int(np.log2(T/(32*1024*1024)))][i] / 1000000, linestyle=" ", marker="o" , color=colors[i]) #, label=layout + ": k = {}".format(threads[i]+1))
        plt.plot(fanouts, comp_cost(fanouts, threads[i] + 1, layout, dev), label=layout + ": k = {}".format(threads[i]+1), color=colors[i])

    
    plt.ylabel("Predicted Latency (sec)")
    plt.xlabel("Growth Factor (F)")
    plt.legend()
    plt.show()


def lookup_cost_by_fanout(dev, layout, db_file_count=900, T=32*1024*1024, cached=True):
    N = T * db_file_count
    fanouts = np.array([x/4 for x in range(8, 64)], dtype=np.float64)
    threads = np.array([1,2,4,8,16,32], dtype=np.float64)

    def read_cost(F, k, layout, dev, cached):
        if cached:
            if layout == "Level":
                return (np.log(N/(C*T)) / np.log(F)) * (cost(k, dev, "_read", 0) + B_ * cost(k, dev, "_read", 1)/B) / 1000000
            elif layout == "Universal":
                return F * (np.log(N/(C*T)) / np.log(F)) * (cost(k, dev, "_read", 0) + B_ * cost(k, dev, "_read", 1)/B) / 1000000
        else:
            if layout == "Level":
                return (np.log(N/(C*T)) / np.log(F)) * (np.log(N/(C*T)) / np.log(F) + 1) * np.log2(C*F) * (cost(k, dev, "_read", 0) + B_ * cost(k, dev, "_read", 1)/B) / 2000000
            elif layout == "Universal":
                return 0

    for i in range(0, 6): 
        # print(read_cost(fanouts, threads[i], layout, dev, cached))
        plt.plot(fanouts, read_cost(fanouts, threads[i], layout, dev, cached), label=layout + ": k = {}".format(threads[i]), color=colors[i])

    
    plt.ylabel("Predicted Latency (sec)")
    plt.xlabel("Growth Factor (F)")
    plt.legend()
    plt.show()

####################################################### END-4







load_data()
# print_data()
fit_data()
# print_models()
# plot_model_params()
# plot_per_thread_models()
# plot_writes_by_access_size()
# plot_by_random_accesses_per_thread()
# plot_by_total_random_accesses()
# plot_model_comparison("Samsung")
# plot_single_model("Samsung", MQSSD_cost, "_write")
# lookup_cost_by_fannout("Samsung")

gen_rocksdb_csv()
load_rocksdb_data(batch_codes=["0003"])
# comp_cost_by_fanout("Samsung", "Level")
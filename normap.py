import math
import matplotlib.pyplot as plt
from random import random
import sys

def generate_number_by_normal():
    mu = 1
    sigma = 2

    u1 = random()
    u2 = random()

    if (u1 <= sys.float_info[3]):
        return generate_number_by_normal()

    mag = sigma * math.sqrt(-2.0 * math.log(u1))
    z0 = mag * math.cos(2*math.pi * u2) + mu
    z1 = mag * math.sin(2*math.pi * u2) + mu
    return [z0, z1]



def generate(a=0, b = 100, size=100):
    result_list = list()
    for i in range(size):
        result_list.extend(generate_number_by_normal())
        # yield round((b - a) * generate_number_by_normal() + a, 0)

        # val = random()
        # yield round((b - a) * val + a, 0)

    return result_list

def plot_list(vals = list()):
    print(vals)
    min_val = min(vals)
    max_val = max(vals)
    r = 10
    step = (max_val - min_val) / (r - 1)

    for i in range(int((max_val - min_val) / step) + 1):
        count = len(list(val for val in vals if min_val + (i) * step <= val < min_val + (i + 1) * step))
        plt.bar(str(min_val + i * step) + ' -- ' + str(min_val + (i+1) * step), count)

    plt.show()

def plot_list_float(vals = list()):
    print(vals)
    min_val = min(vals)
    max_val = max(vals)
    r = 10
    step = round((max_val - min_val) / (r - 1), 0)

    for i in range(r):
        count = len(list(val for val in vals if min_val + (i) * step <= val < min_val + (i + 1) * step))
        plt.bar(str(round(min_val + i * step, 2)) + ' -- ' + str(round(min_val + (i+1) * step, 2)), count)

    plt.show()


plot_list_float(generate(0, 10, 1000))
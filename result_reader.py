import pandas as pd
import os
import numpy as np
from datetime import datetime
import pyansys


def calc_avg_load(n: int, row):
    # rst_path = "D:\\master degree\\balk-analyzer\\researches\\" + str(n) + "_angle" + os.sep + str(int(row.research_id)) + os.sep + "file.rst"
    rst_path = "D:\\lab1" + os.sep + "file.rst"
    print(rst_path)
    principal_result_stress = pyansys.read_binary(rst_path).principal_nodal_stress(0)
    result_stress = pyansys.read_binary(rst_path).nodal_stress(0)

    seqv = np.array(list(map(lambda v: 0 if np.isnan(v) else v, principal_result_stress[1][:,4])))
    sx = np.array(list(map(lambda v: 0 if np.isnan(v) else v, result_stress[1][:, 0])))
    sy = np.array(list(map(lambda v: 0 if np.isnan(v) else v, result_stress[1][:, 1])))
    sz = np.array(list(map(lambda v: 0 if np.isnan(v) else v, result_stress[1][:, 2])))

    return np.array([seqv.mean(), sx.mean(), sy.mean(), sz.mean()])


def process_n_angle_result(n: int):
    start = datetime.now()
    res = pd.read_csv(str(n) + "_angle_research_list.csv")
    for i, row in res.iterrows():
        seqv_sx_sy_sz = calc_avg_load(n, row)
        res.at[i, "avg_seqv"] = seqv_sx_sy_sz[0]
        res.at[i, "avg_sx"] = seqv_sx_sy_sz[1]
        res.at[i, "avg_sy"] = seqv_sx_sy_sz[2]
        res.at[i, "avg_sz"] = seqv_sx_sy_sz[3]

    print(res)
    res.to_csv(str(n) + "_angle_processed_results.csv")

    end = datetime.now()
    print("diff: " + str(end - start))


if __name__ == "__main__":
    seqv_sx_sy_sz = calc_avg_load(None, None)
    res = dict()
    res["avg_seqv"] = seqv_sx_sy_sz[0]
    res["avg_sx"] = seqv_sx_sy_sz[1]
    res["avg_sy"] = seqv_sx_sy_sz[2]
    res["avg_sz"] = seqv_sx_sy_sz[3]
    print(res)
    # angles = [0]
    # for a in angles:
    #     process_n_angle_result(a)
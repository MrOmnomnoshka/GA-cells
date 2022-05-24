import ansys.mapdl.reader as pyansys
import numpy as np
import pandas as pd


def show_stress_chart(file_name):
    print('FILE NAME: ' + file_name)
    result_stress = pyansys.read_binary(file_name).nodal_stress(0)
    principal_result_stress = pyansys.read_binary(file_name).principal_nodal_stress(0)

    nodes = {}
    for i in range(len(result_stress[1])):
        key = i + 1
        if nodes.get(key) is None:
            value = {
                "node": key,
                "x": 0 if np.isnan(result_stress[1][i][0]) else result_stress[1][i][0],
                "y": 0 if np.isnan(result_stress[1][i][1]) else result_stress[1][i][1],
                "z": 0 if np.isnan(result_stress[1][i][2]) else result_stress[1][i][2],
                "xy": 0 if np.isnan(result_stress[1][i][3]) else result_stress[1][i][3],
                "yz": 0 if np.isnan(result_stress[1][i][4]) else result_stress[1][i][4],
                "xz": 0 if np.isnan(result_stress[1][i][5]) else result_stress[1][i][5],
                "eqv":  0 if np.isnan(principal_result_stress[1][i][4]) else principal_result_stress[1][i][4],
            }
            nodes[key] = value
    res = pd.DataFrame(data=nodes).transpose()

    import plotly.graph_objects as go

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=res['node'].values.tolist(), y=res["x"].values.tolist(), mode="lines", name="x"))
    figure.add_trace(go.Scatter(x=res['node'].values.tolist(), y=res["y"].values.tolist(), mode="lines", name="y"))
    figure.add_trace(go.Scatter(x=res['node'].values.tolist(), y=res["z"].values.tolist(), mode="lines", name="z"))
    figure.add_trace(go.Scatter(x=res['node'].values.tolist(), y=res["eqv"].values.tolist(), mode="lines", name="eqv"))

    figure.show()

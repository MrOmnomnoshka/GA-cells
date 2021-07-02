import numpy as np
from ansys.mapdl import reader

def calculate_avg_and_max_stress(file: str):
    _, stress = reader.read_binary(file).principal_nodal_stress(0)
    stress = stress[:, 4]
    stress = stress[~np.isnan(stress)]

    avg_stress = np.average(stress)
    max_stress = np.max(stress)
    return avg_stress, max_stress
if __name__ == "__main__":
    import sys
    import ansys.mapdl.reader as pyansys

    file_name = sys.argv[1]
    print('FILE NAME: ' + file_name)
    res = pyansys.read_binary(file_name)
    res.plot_nodal_solution(0, 'x', label='Displacement')

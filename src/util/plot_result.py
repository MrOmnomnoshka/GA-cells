if __name__ == "__main__":
    import sys
    import ansys.mapdl.reader as pyansys

    file_name = sys.argv[1]
    res = pyansys.read_binary(file_name)
    res.plot_principal_nodal_stress(0, 'seqv', cpos="xy")  # , cpos="xy")  # , True)

    res.plot_principal_nodal_stress(0, 'seqv', True, cpos="xy")
    res.animate_nodal_solution(0, n_frames=200, cpos="xy")

    # Other working options
    # res.plot(0)
    # res.plot_principal_nodal_stress(0, 'seqv', True, 1.0)  # ['S1', 'S2', 'S3', 'SINT', 'SEQV']
    # res.plot_nodal_elastic_strain(0, "EQV")  # ['X', 'Y', 'Z', 'XY', 'YZ', 'XZ', 'EQV']
    # res.plot_nodal_solution(0)  # None or ['UX', 'UY', 'UZ']
    # res.plot_nodal_displacement(0, show_displacement=True)  # None or ['UX', 'UY', 'UZ']
    # res.plot_nodal_stress(0, 'xz')

    """ more at: https://docs.pyvista.org/api/plotting/index.html """

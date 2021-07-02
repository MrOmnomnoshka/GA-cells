import json
import os
import sys

import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as a3
import numpy as np
import scipy as sp
from mpl_toolkits.mplot3d import Axes3D
from scipy import spatial as sp_spatial
import pandas as pd


def calculate_faces(nodes: set, research_folder: str):

    points = np.genfromtxt(fname=research_folder + os.sep + "nodes.csv", skip_header=1, delimiter=",", usecols=(1, 2, 3))
    points_ids = np.genfromtxt(fname=research_folder + os.sep + "nodes.csv", skip_header=1, delimiter=",", usecols=[0])
    return points

    tri = sp_spatial.Delaunay(points)
    indices = tri.convex_hull
    if len(nodes) > 0:
        indices = np.array(list(filter(lambda face: len(set(face) & nodes) > 0, indices)))

    faces = points[indices]

    used_ids = set([x for t in indices for x in t])
    print("Unused points: ", len(set(points_ids) - used_ids))

    cells_coordinates = []
    with open(research_folder + os.sep + "cells.json") as f_in:
        cells_coordinates = json.load(f_in)

    if len(cells_coordinates) > 0:
        return [x for x in faces if not is_face_in_cell(x, cells_coordinates)]

    return faces

def is_face_in_cell(face, cells_coordinates):
    p1x = p2x = p3x = p1y = p2y = p3y = False
    if face[0][2] == face[1][2] == face[2][2]:
        for cell_coordinates in cells_coordinates:
            for coordinate in cell_coordinates:
                x = float(coordinate["x"])
                y = float(coordinate["y"])

                if round(face[0][0],4) == round(x,4):
                    p1x = True
                if round(face[1][0],4) == round(x,4):
                    p2x = True
                if round(face[2][0],4) == round(x,4):
                    p3x = True
                if round(face[0][1],4) == round(y,4):
                    p1y = True
                if round(face[1][1],4) == round(y,4):
                    p2y = True
                if round(face[2][1],4) == round(y,4):
                    p3y = True

                if p1x and p2x and p3x and p1y and p2y and p3y:
                    return True

    return p1x or p2x or p3x or p1y or p2y or p3y

if __name__ == "__main__":
    research_folder = sys.argv[1]
    picked_nodes_ids = set(json.loads(sys.argv[2]))
    faces = calculate_faces(set(picked_nodes_ids), research_folder)

    point_pd = pd.DataFrame(data=faces, columns=["x","y","z"])

    fig = plt.figure()
    ax = Axes3D(fig)

    ax.scatter(faces[:,0], faces[:,1], faces[:,2])
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    plt.show()



    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.dist = 20
    # ax.azim = 0
    # ax.set_xlabel('x')
    # ax.set_ylabel('y')
    # ax.set_zlabel('z')
    #
    # max_x = 0
    # max_y = 0
    # max_z = 0
    # for f in faces:
    #     face = a3.art3d.Poly3DCollection([f])
    #     face.set_color(mpl.colors.rgb2hex(sp.rand(3)))
    #     face.set_edgecolor('k')
    #     face.set_alpha(0.5)
    #     ax.add_collection3d(face)
    #
    #     for p in f:
    #         if p[0] > max_x:
    #             max_x = p[0]
    #         if p[1] > max_y:
    #             max_y = p[1]
    #         if p[2] > max_z:
    #             max_z = p[2]
    #
    # ax.set_xlim([0, math.ceil(max_x)])
    # ax.set_ylim([0, math.ceil(max_y)])
    # ax.set_zlim([0, math.ceil(max_z)])
    #
    # plt.show()
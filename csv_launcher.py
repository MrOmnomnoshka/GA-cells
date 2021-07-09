import csv
import os
import sys

from BodyParams import BodyParameters
from Calculation import CalculationParams, Calculation
from Cells import CircleCells, NAngleCells


def parse_row_to_calc_params(row):
    return CalculationParams(
        angle_num=int(row[1]),
        rotate_angle=int(row[2]),
        volume_part=int(row[3]),
        cells_ox=int(row[4]),
        cells_oy=int(row[5])
    )

if __name__ == "__main__":
    angles = [5]
    for a in angles:
        file_name = str(a) + "_angle_research_list.csv"
        with open(file = file_name, mode = "r") as research_list_file:
            with open(file= str(a) + "_angle_result_researches.csv", mode="a", newline="") as result_researches:
                result_researches.write(research_list_file.readline())
            reader = csv.reader(research_list_file)


            for row in reader:
                body_params = BodyParameters(0, 250, 0, 250, 10, 240)
                calc_params = parse_row_to_calc_params(row)
                if calc_params.angle_num < 3:
                    cells = CircleCells(body_params)
                else:
                    cells = NAngleCells(body_params)
                    cells.angle_num = calc_params.angle_num

                cells.columns = calc_params.cells_ox
                cells.rows = calc_params.cells_oy
                cells.cell_height = body_params.height
                cells.v_cells = body_params.v * calc_params.volume_part / 100
                cells.rotation_angle = calc_params.rotate_angle
                cells.calculation()

                calculation = Calculation([sys.argv[1]], [sys.argv[2]])

                with open(file= str(a) + "_angle_result_researches.csv", mode="a", newline="") as result_researches:
                    writer = csv.writer(result_researches)

                    if calculation.researchFromDetailModel(body_params, calc_params, cells, "D:\\master degree\\balk-analyzer\\researches\\" + str(a) + "_angle" + os.sep + row[0], None, int(row[0])):
                        writer.writerow(row + ["FINISHED"])
                    else:
                        writer.writerow(row + ["FAILED"])

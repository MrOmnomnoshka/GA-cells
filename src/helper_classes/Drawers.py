import src.util.ansys_parser as ansys_parser
import src.constants as constants


# TODO(BIG!): Генерировать зону не выходя за рамки детали, что бы не ломать "корпус" модели (по крайней мере когда...
# TODO: # ...модель позволяет)


class PerfectCellsDrawer:
    def __init__(self, cells_params, ansys):
        self.cells = cells_params
        self.ansys = ansys

    def draw_cells_volumes(self):
        x_offset = (self.cells.width - self.cells.diameter * self.cells.n_ox) / (self.cells.n_ox + 1)
        y_offset = (self.cells.length - self.cells.diameter * self.cells.n_oy) / (self.cells.n_oy + 1)

        for i in range(0, self.cells.n_oy):
            for j in range(0, self.cells.n_ox):
                x = self.cells.x0 + (j + 1) * x_offset + (2 * j + 1) * self.cells.radius
                y = self.cells.y0 + (i + 1) * y_offset + (2 * i + 1) * self.cells.radius

                # Move WP to a XYZ coordinate  # TODO: combine those two commands in "one that rules them all!"
                self.ansys.run(f"WPLANE, -1, {x}, {y}")

                # Rotate working plain OY by an angle
                self.ansys.run(f"WPRO,{self.cells.rotation_angle}")

                if self.cells.angle_num == constants.AN_MAX:  # High Angle num is tends to be cylinder
                    # Creating a circular cell
                    cell_creation_command = f"CYLIND,{self.cells.radius}, ,{self.cells.z0},{self.cells.z1}"
                else:
                    # Creating N-angle prism by circumscr radius
                    cell_creation_command = f"RPRISM,{self.cells.z0},{self.cells.z1}," \
                                            f"{self.cells.angle_num},,{self.cells.radius}"

                output = self.ansys.run(cell_creation_command)

                if constants.SYMMETRY_OY:  # TODO: make symmetry in the end by volume id
                    v_id = int(ansys_parser.get_element_ids(output)[0])
                    self.ansys.run("FLST, 3, 1, 6, ORDE, 1")
                    self.ansys.run(f"FITEM, 3, {v_id}")
                    self.ansys.run("VSYMM, X, P51X,,,, 0, 0")

from src.helper_classes.TableHeaders import TableHeaders
import src.constants as constants


class CellParams:
    def __init__(self, table__data):
        self.angle_num = int(table__data[TableHeaders.ANGLE_NUM])
        self.rotation_angle = int(table__data[TableHeaders.ROTATE_ANGLE])
        self.volume_part = int(table__data[TableHeaders.VOLUME_PART])
        self.n_ox = int(table__data[TableHeaders.CELLS_OX])
        self.n_oy = int(table__data[TableHeaders.CELLS_OY])
        self.x0 = float(table__data[TableHeaders.DETAIL_X0])
        self.x1 = float(table__data[TableHeaders.DETAIL_X1])
        self.y0 = float(table__data[TableHeaders.DETAIL_Y0])
        self.y1 = float(table__data[TableHeaders.DETAIL_Y1])
        self.z0 = float(table__data[TableHeaders.DETAIL_Z0])
        self.z1 = float(table__data[TableHeaders.DETAIL_Z1])

    def calculate_all(self):
        self.calculate_params()
        self.calculate_radius()

    def calculate_params(self):
        self.width = self.x1 - self.x0
        self.length = self.y1 - self.y0
        self.height = self.z1 - self.z0
        self.square = self.length * self.width
        self.volume = self.square * self.height

        self.amount = self.n_ox * self.n_oy

    def calculate_radius(self):
        r_x = self.width / (self.n_ox * 2)
        r_y = self.length / (self.n_oy * 2)
        full_radius = min(r_x, r_y)
        self.radius = full_radius * self.volume_part / 100
        self.diameter = self.radius * 2

import math

from src.helper_classes.Cells import CircleCells
import src.util.ansys_parser as ansys_parser


class AbstractNAngleDrawers:

    def __init__(self, body, angle, ansys):
        self._ansys = ansys
        self.point_service = PointService(self._ansys)
        self.line_service = LineService(self._ansys)
        self.plain_service = PlainService(self.line_service, self._ansys)

        self._body = body
        self._deflection_angle = angle * math.pi / 180

    def subtract_plain(self, points, plain_id):
        point_ids = []
        for point in points:
            point_ids.append(self.point_service.add(point["x"], point["y"]))

        removed_plain_id = self.plain_service.add(point_ids)
        return self.plain_service.remove_plain_from_plain(plain_id, removed_plain_id)

    def calc_points(self, x0, y0, x_end, y_end, n):
        angle_0 = math.atan2(y_end - y0, x_end - x0)
        points = []
        r = math.sqrt((x_end - x0) ** 2 + (y_end - y0) ** 2)
        for i in range(n):
            angle = 2 * math.pi * i / n + angle_0
            x = r * math.cos(angle) + x0
            y = r * math.sin(angle) + y0

            points.append({"x": x, "y": y})

        return points

    def draw_cells_based_on_main_plain(self, plain_id):
        pass

    def draw_cells_volumes(self):
        pass

    def set_cells(self, cells):
        self._cells = cells

    def get_deflection(self):
        return self._deflection_angle


class NAngleCellsDrawer(AbstractNAngleDrawers):

    def __init__(self, body, angle, ansys):
        super().__init__(body, angle, ansys)

    def draw_cells_volumes(self):
        cells_coordinates = list()

        available_body_len = self._body.x1 - self._body.x0
        len_x = (available_body_len - 2 * self._cells.radius * self._cells.columns) / (self._cells.columns + 1)
        len_y = (self._body.width - 2 * self._cells.radius * self._cells.rows) / (self._cells.rows + 1)

        for i in range(0, self._cells.rows):
            current_y = self._body.y0 + (i + 1) * len_y + (2 * i + 1) * self._cells.radius

            for j in range(0, self._cells.columns):
                current_x = self._body.x0 + (j + 1) * len_x + (2 * j + 1) * self._cells.radius
                points = self.calc_points_for_n_angle_cell_at_coordinate(current_x, current_y)

                point_ids = []
                for point in points:
                    point_ids.append(self.point_service.add(point["x"], point["y"], self._body.z0))

                cell_plain_id = self.plain_service.add(point_ids)
                self._ansys.voffst(cell_plain_id, self._body.height)

                cells_coordinates.append(points)

        return cells_coordinates

    # x0 and y0 are center of the figure
    def calc_points_for_n_angle_cell_at_coordinate(self, x0, y0):
        delta_angle = 2 * math.pi / self._cells.angle_num
        rotate_angle_rad = self._cells.rotation_angle * math.pi / 180

        points = []

        current_angle = 0
        while current_angle < 2 * math.pi - 0.05:
            x = x0 + self._cells.radius * math.cos(current_angle + rotate_angle_rad)
            y = y0 + self._cells.radius * math.sin(current_angle + rotate_angle_rad)

            current_angle += delta_angle

            points.append({"x": x, "y": y})

        if (points[0]["x"] == points[len(points) - 1]["x"]) and (points[0]["y"] == points[len(points) - 1]["y"]):
            points.pop(len(points) - 1)
        return points


class RectangleCellsDrawer(AbstractNAngleDrawers):

    def __init__(self, body, angle, ansys):
        super().__init__(body, angle, ansys)

    def draw_cells_volumes(self):

        cells_coordinates = list()

        len_x = (self._body.length - self._cells.cell_length * self._cells.columns) / (self._cells.columns + 1)
        len_y = (self._body.width - self._cells.cell_width * self._cells.rows) / (self._cells.rows + 1)

        for i in range(1, self._cells.rows + 1):
            for j in range(1, self._cells.columns + 1):
                x0_j = self._body.x0 + j * len_x + (j - 1) * self._cells.cell_length
                x1_j = self._body.x0 + j * (len_x + self._cells.cell_length)

                y0_i = self._body.y0 + i * len_y + (i - 1) * self._cells.cell_width
                y1_i = self._body.y0 + i * (len_y + self._cells.cell_width)

                points = [
                    {"x": x0_j, "y": y0_i},
                    {"x": x0_j, "y": y1_i},
                    {"x": x1_j, "y": y1_i},
                    {"x": x1_j, "y": y0_i}
                ]

                point_ids = []
                for point in points:
                    point_ids.append(self.point_service.add(point["x"], point["y"], self._body.z1))

                cells_coordinates.append(points)
                cell_plain_id = self.plain_service.add(point_ids)
                self._ansys.voffst(cell_plain_id, self._body.height)
                # result_plain_id = self.subtract_plain(points, result_plain_id)

        return cells_coordinates
        # return result_plain_id

    def set_cells(self, cells):
        self._cells = cells


class CircleCellsDrawer(AbstractNAngleDrawers):

    def __init__(self, body, angle, ansys):
        super().__init__(body, angle, ansys)

    def draw_cells_volumes(self):
        cells_coordinates = list()

        available_body_len = self._body.x1 - self._body.x0
        len_x = (available_body_len - 2 * self._cells.radius * self._cells.columns) / (self._cells.columns + 1)
        len_y = (self._body.width - 2 * self._cells.radius * self._cells.rows) / (self._cells.rows + 1)

        for i in range(0, self._cells.rows):
            current_y = self._body.y0 + (i + 1) * len_y + (2 * i + 1) * self._cells.radius

            for j in range(0, self._cells.columns):
                current_x = self._body.x0 + (j + 1) * len_x + (2 * j + 1) * self._cells.radius

                # CYL4, x, y, r
                command = f"CYL4, {current_x}, {current_y}, {self._cells.radius}"
                output = self._ansys.run(command)
                cell_plain_id = ansys_parser.get_element_id(output)

                self._ansys.voffst(cell_plain_id, self._body.height)

                cells_coordinates.append({"x": current_x, "y": current_y})

        return cells_coordinates

    # x0 and y0 are center of the figure
    def calc_points_for_n_angle_cell_at_coordinate(self, x0, y0):
        delta_angle = 2 * math.pi / self._cells.angle_num
        rotate_angle_rad = self._cells.rotation_angle * math.pi / 180

        points = []

        current_angle = 0
        while current_angle < 2 * math.pi - 0.05:
            x = x0 + self._cells.radius * math.cos(current_angle + rotate_angle_rad)
            y = y0 + self._cells.radius * math.sin(current_angle + rotate_angle_rad)

            current_angle += delta_angle

            points.append({"x": x, "y": y})

        if (points[0]["x"] == points[len(points) - 1]["x"]) and (points[0]["y"] == points[len(points) - 1]["y"]):
            points.pop(len(points) - 1)
        return points


class PointService:
    __id = 0

    def __init__(self, ansys):
        self.__ansys = ansys
        super().__init__()

    def add(self, x0, y0, z0=0):
        try:
            self.__id = ansys_parser.get_max_element_id_from_command(self.__ansys, "KP")
        except Exception:
            self.__id = 0

        self.__id += 1

        self.__ansys.k(self.__id, x0, y0, z0)

        return self.__id


class LineService:
    __id = 0

    def __init__(self, ansys):
        self.__ansys = ansys
        super().__init__()

    def add(self, point1, point2):
        self.__id = self.__ansys.l(point1, point2)
        return self.__id


class PlainService:
    __id = 0
    __used_ids = set()

    def __init__(self, line_service, ansys):
        self.__line_service = line_service
        self.__ansys = ansys
        super().__init__()

    def add(self, points):
        lines = []
        for i in range(len(points)):
            if i < len(points) - 1:
                line_id = self.__line_service.add(points[i], points[i + 1])
            else:
                line_id = self.__line_service.add(points[i], points[0])
            lines.append(line_id)

        command = "A,%s" % (", ".join([str(point_id) for point_id in points]))
        output = self.__ansys.run(command)
        self.__id = ansys_parser.get_element_id(output)
        return self.__id

    def remove_plain_from_plain(self, plain_id, removed_plain_id):
        self.__ansys.asba(plain_id, removed_plain_id)

        id = self.__get_id()
        self.__used_ids.remove(plain_id)
        self.__used_ids.remove(removed_plain_id)

        return id

    def get_max_id(self):
        res = self.__ansys.run("*GET, KMax, AREA,, NUM, MAX")
        start = res.index("VALUE= ") + 7
        max = res[start:]
        return max

    def __get_id(self):
        difference = set(range(1, self.__id + 1)) \
            .difference(self.__used_ids)

        if len(difference) == 0:
            self.__id += 1
            id = self.__id
        else:
            id = min(difference)

        self.__used_ids.add(id)
        return id


class VolumeService:

    def __init__(self, line_service, ansys):
        self.__line_service = line_service
        self.__ansys = ansys
        super().__init__()

    def voffst_area(self, area_id, dist):
        self.__ansys.voffst(area_id, dist, 0)

    def get_max_id(self):
        res = self.__ansys.run("*GET, KMax, VOLU,, NUM, MAX")
        start = res.index("VALUE= ") + 7
        max = res[start:]
        return max

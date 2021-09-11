from abc import ABC, abstractmethod
from math import pi, sin, sqrt
from src.researches.BodyParams import *


class AbstractAngle(ABC):

    body = BodyParameters(0, 0, 0, 0, 0, 0)
    accuracy = 7
    columns = rows = 0
    side = 0
    angle_num = 0
    cell_height = 0
    local = 0
    s_cells = s_cell = 0
    radius = 0
    availability = False
    v_cells = 0
    rotation_angle = 0
    info = ""

    def __init__(self, body):
        self.body = body

    @abstractmethod
    def calculation(self):
        pass

    def try_size_condition(self):
        self.local = self.body.width / self.columns
        buf = self.body.length / self.rows
        return self.local == buf


class AbstractRelationAngle(AbstractAngle, ABC):

    k_x = k_y = 0
    max_c = pi / 4
    relation = 0

    def __init__(self, body):
        super().__init__(body)


class CircleCells(AbstractRelationAngle):

    def __init__(self, boby_params):
        super().__init__(boby_params)
        self.angle_num = 0

    def calculation(self):
        if not self.try_size_condition():
            return

        self.s_cells = self.v_cells / self.cell_height
        self.s_cell = self.s_cells / (self.rows * self.columns)

        self.radius = (self.s_cell/pi)**0.5
        self.k_x = (self.body.width - self.radius * 2 * self.rows)/(self.rows + 1)
        self.k_y = (self.body.length - self.radius * 2 * self.columns)/(self.columns + 1)

    def try_size_condition(self):
        return self.radius * 2 * self.rows \
               < self.body.width and self.radius * 2 * self.columns \
               < self.body.length


class RectangleCells(AbstractAngle):

    k = 0
    v_cell_fact = 0
    cell_width = cell_length = 0

    def __init__(self, body_params):
        super().__init__(body_params)
        self.angle_num = 4

    def calculation(self):

        self.s_cells = self.v_cells / self.cell_height
        self.s_cell = self.s_cells / (self.rows * self.columns)

        coef = self.s_cell / (self.body.width * self.body.length)

        self.cell_length = self.body.length * sqrt(coef)
        self.cell_width = self.body.width * sqrt(coef)

        # TODO: add size of angle

    def try_size_condition(self):
        return True

    def get_root(self, a, b, c):
        d = b**2 - 4 * a * c
        if d < 0:
            return -1
        elif d == 0:
            # -b / 2a
            self.k = -b / 2 / a
            self.cell_length = (self.body.length - self.k * (self.columns + 1)) / self.columns
            self.cell_width = (self.body.width - self.k * (self.rows + 1)) / self.rows

            if round((self.cell_length * self.cell_width), 2) == round(self.s_cell, 2):
                return 1
            else:
                return -1
        else:
            self.k = (-b + d**0.5) / (2 * a)
            self.cell_length = abs(self.body.length - self.k * (self.columns + 1)) / self.columns
            self.cell_width = abs(self.body.width - self.k * (self.rows + 1)) / self.rows
            if self.cell_length > 0 and self.cell_width > 0 and \
                    round((self.cell_length * self.cell_width), 2) == round(self.s_cell, 2):
                return 1
            self.k = (-b - d ** 0.5) / 2 * a
            self.cell_length = abs(self.body.length - self.k * (self.columns + 1)) / self.columns
            self.cell_width = abs(self.body.width - self.k * (self.rows + 1)) / self.rows
            if self.cell_length > 0 and self.cell_width > 0 and \
                    round((self.cell_length * self.cell_width), 2) == round(self.s_cell, 2):
                return 1
            return -1


class NAngleCells(AbstractRelationAngle):

    def __init__(self, body_params):
        super().__init__(body_params)

    def calculation(self):
        self.s_cells = self.v_cells / self.cell_height
        self.s_cell = self.s_cells / (self.rows * self.columns)

        # Иногда тут ZeroDivisionError, но вобще было без комента, хоть и бесполезно
        # coef = self.s_cell / (self.body.width * self.body.length)

        # size of angle
        angle_rad = 2 * pi / self.angle_num
        # Formula of circle radius about N angle figure
        self.radius = sqrt(2*self.s_cell/(self.angle_num*sin(angle_rad)))

    def try_size_condition(self):
        return self.radius * 2 * self.rows \
               < self.body.width and self.radius * 2 * self.columns \
               < self.body.length

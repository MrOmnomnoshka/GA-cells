from random import randint, random
from math import ceil
import src.constants as constants


class Chromosome:
    def __init__(self, working_zone=tuple, angles=int, rotation=int, size=int, x_amount=int, y_amount=int, depth=False):
        self.working_zone = working_zone  # TODO: Note: w_z is only in INT, redo to FLOAT? (can't research small models)
        self.angles = angles
        self.rotation = rotation
        self.size = size
        self.x_amount = x_amount
        self.y_amount = y_amount
        self.depth = depth
        # TODO?: ?subdivide working_zone to 4 parameters (x0,x1,y0,y1)

    def generate_all_params(self):
        self.generate_working_zone()
        self.generate_cells_angles()
        self.generate_cells_rotation()
        self.generate_cells_size()
        self.generate_cells_amount()

    def mutate_all_parameters(self):
        self._mutate_working_zone()
        self._mutate_cells_angles()
        self._mutate_cells_rotation()
        self._mutate_cells_size()
        self._mutate_cells_amount()

    def crossover_two_parents(self, parent1, parent2):
        for param in vars(self):
            parent = self._random_parent_select(parent1, parent2)
            parameter = getattr(parent, param)
            setattr(self, param, parameter)

    def _random_parent_select(self, parent1, parent2):
        if random() <= 0.5:
            return parent1
        else:
            return parent2

    def generate_working_zone(self):
        x_start = randint(constants.X_MIN, constants.X_MAX - 1)
        x_end = randint(x_start + 1, constants.X_MAX)

        y_start = randint(constants.Y_MIN, constants.Y_MAX - 1)
        y_end = randint(y_start + 1, constants.Y_MAX)

        x_size = x_start, x_end
        y_size = y_start, y_end

        if self.depth:
            z_start = randint(constants.Z_MIN, constants.Z_MAX - 1)
            z_end = randint(z_start + 1, constants.Z_MAX)
            z_size = z_start, z_end
            self.working_zone = (x_size, y_size, z_size)
        else:
            self.working_zone = (x_size, y_size)

    def generate_cells_angles(self):
        self.angles = randint(constants.AN_MIN, constants.AN_MAX)

    def generate_cells_rotation(self):
        self.rotation = randint(constants.RT_MIN, constants.RT_MAX)

    def generate_cells_size(self):
        self.size = randint(constants.SZ_MIN, constants.SZ_MAX)

    def generate_cells_amount(self):
        self.x_amount = randint(constants.XA_MIN, constants.XA_MAX)
        self.y_amount = randint(constants.YA_MIN, constants.YA_MAX)

    def _mutate_working_zone(self):
        x_size = self._mutate_x_size()
        y_size = self._mutate_y_size()

        if self.depth:
            z_size = self._mutate_z_size()
            self.working_zone = x_size, y_size, z_size
        else:
            self.working_zone = x_size, y_size

    def _mutate_x_size(self):
        start, stop = self.working_zone[0]
        start = self.__mutate_parameter(constants.X_MIN, constants.X_MAX, start)
        stop = self.__mutate_parameter(constants.X_MIN, constants.X_MAX, stop)
        if start == stop:
            return self._mutate_x_size()
        return min(start, stop), max(start, stop)

    def _mutate_y_size(self):
        start, stop = self.working_zone[1]
        start = self.__mutate_parameter(constants.Y_MIN, constants.Y_MAX, start)
        stop = self.__mutate_parameter(constants.Y_MIN, constants.Y_MAX, stop)
        if start == stop:
            return self._mutate_y_size()
        return min(start, stop), max(start, stop)

    def _mutate_z_size(self):
        start, stop = self.working_zone[2]
        start = self.__mutate_parameter(constants.Z_MIN, constants.Z_MAX, start)
        stop = self.__mutate_parameter(constants.Z_MIN, constants.Z_MAX, stop)
        if start == stop:
            return self._mutate_z_size()
        return min(start, stop), max(start, stop)

    def _mutate_cells_angles(self):
            self.angles = self.__mutate_parameter(constants.AN_MIN, constants.AN_MAX, self.angles)

    def _mutate_cells_rotation(self):
        self.rotation = self.__mutate_parameter(constants.RT_MIN, constants.RT_MAX, self.rotation)

    def _mutate_cells_size(self):
        self.size = self.__mutate_parameter(constants.SZ_MIN, constants.SZ_MAX, self.size)

    def _mutate_cells_amount(self):
        self.x_amount = self.__mutate_parameter(constants.XA_MIN, constants.XA_MAX, self.x_amount)
        self.y_amount = self.__mutate_parameter(constants.YA_MIN, constants.YA_MAX, self.y_amount)

    def __mutate_parameter(self, p_min, p_max, parameter):
        mut_value = self.__create_mut_value_for_parameter(p_min, p_max)
        return self.__check_borders(parameter + randint(-mut_value, mut_value), p_min, p_max)

    def __create_mut_value_for_parameter(self, v_min, v_max):
        return ceil((v_max - v_min) * constants.MUT_SIZE / 100)  # Ceil - due to small values can't mutate

    def __check_borders(self, value, v_min, v_max):
        value = max(value, v_min)
        value = min(value, v_max)
        return value

    def __str__(self):
        string = \
            f"{self.__repr__()}" \
            f"\nWorking zone: {self.working_zone} " \
            f"\nAngles: {self.angles}" \
            f"\nRotation: {self.rotation}" \
            f"\nSize: {self.size}" \
            f"\nAmount (x, y): {self.x_amount}, {self.y_amount}"
        return string

from random import randint, uniform, random
from math import ceil
import src.constants as constants


class Agent:
    def __init__(self, angles=int, rotation=int, size=int, x_amount=int, y_amount=int, working_zone=tuple(tuple())):
        self.angles = angles
        self.rotation = rotation
        self.size = size
        self.x_amount = x_amount
        self.y_amount = y_amount
        self.working_zone = working_zone  # TODO?: mb subdivide working_zone to 6 parameters (x0,x1,y0,y1,z0,z1)

        self.depth = constants.CELLS_DEPTH

    def generate_all_params(self):
        self.generate_cells_angles()
        self.generate_cells_rotation()
        self.generate_cells_size()
        self.generate_cells_amount()
        self.generate_working_zone()

    def mutate_all_parameters(self):
        self._mutate_cells_angles()
        self._mutate_cells_rotation()
        self._mutate_cells_size()
        self._mutate_cells_amount()
        self._mutate_working_zone()

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

    def generate_cells_angles(self):
        self.angles = randint(constants.AN_MIN, constants.AN_MAX)

    def generate_cells_rotation(self):
        self.rotation = randint(constants.RT_MIN, constants.RT_MAX)

    def generate_cells_size(self):
        self.size = randint(constants.SZ_MIN, constants.SZ_MAX)

    def generate_cells_amount(self):
        self.x_amount = randint(constants.XA_MIN, constants.XA_MAX)
        self.y_amount = randint(constants.YA_MIN, constants.YA_MAX)

    def generate_working_zone(self):
        x_start, x_end = self._generate_start_end(constants.X_MIN, constants.X_MAX)
        y_start, y_end = self._generate_start_end(constants.Y_MIN, constants.Y_MAX)

        if self.depth:
            z_start, z_end = self._generate_start_end(constants.Z_MIN, constants.Z_MAX)
        else:
            z_start, z_end = float(constants.Z_MIN), float(constants.Z_MAX)

        x_size = x_start, x_end
        y_size = y_start, y_end
        z_size = z_start, z_end

        self.working_zone = (x_size, y_size, z_size)

    def _generate_start_end(self, a, b):
        start, end = round(uniform(a, b), 1), round(uniform(a, b), 1)
        if start > end:  # swap to it's place if needed
            start, end = end, start
        return start, end

    def _mutate_cells_angles(self):
            self.angles = round(self.__mutate_parameter(constants.AN_MIN, constants.AN_MAX, self.angles))

    def _mutate_cells_rotation(self):
        self.rotation = round(self.__mutate_parameter(constants.RT_MIN, constants.RT_MAX, self.rotation))

    def _mutate_cells_size(self):
        self.size = round(self.__mutate_parameter(constants.SZ_MIN, constants.SZ_MAX, self.size))

    def _mutate_cells_amount(self):
        self.x_amount = round(self.__mutate_parameter(constants.XA_MIN, constants.XA_MAX, self.x_amount))
        self.y_amount = round(self.__mutate_parameter(constants.YA_MIN, constants.YA_MAX, self.y_amount))

    def _mutate_working_zone(self):
        x_size = self._mutate_coords(self.working_zone[0], constants.X_MIN, constants.X_MAX)
        y_size = self._mutate_coords(self.working_zone[1], constants.Y_MIN, constants.Y_MAX)

        if self.depth:
            z_size = self._mutate_coords(self.working_zone[2], constants.Z_MIN, constants.Z_MAX)
        else:
            z_size = self.working_zone[2]

        self.working_zone = x_size, y_size, z_size

    def _mutate_coords(self, coords, min_v, max_v):
        start, stop = coords
        start = round(self.__mutate_parameter(min_v, max_v, start), 1)
        stop = round(self.__mutate_parameter(min_v, max_v, stop), 1)
        if start == stop:  # remutate if equal
            return self._mutate_coords(coords, min_v, max_v)
        if start > stop:  # swap to it's place if needed
            start, stop = stop, start
        return start, stop

    def __mutate_parameter(self, p_min, p_max, parameter):
        mut_value = self.__create_mut_value_for_parameter(p_min, p_max)
        return self.__check_borders(parameter + uniform(-mut_value, mut_value), p_min, p_max)

    def __create_mut_value_for_parameter(self, v_min, v_max):
        mut_value = (v_max - v_min) * constants.MUT_SIZE / 100  # Mutate on a range*mut_size(%)
        return ceil(mut_value)  # Ceil - due to small values can't mutate

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
            f"\nAmount (x, y): {self.x_amount}, {self.y_amount}" \
            f"\nDepth: {self.depth}"
        return string

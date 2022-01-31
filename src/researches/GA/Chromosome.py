from random import randint, random
from math import ceil


class Chromosome:
    mut_percentage = 5

    # TODO: auto-make x, y, z for BodySize
    x_min, x_max = 10, 240
    y_min, y_max = 10, 240
    z_min, z_max = 0, 250

    an_min, an_max = 3, 8  # 8
    rt_min, rt_max = 0, 360
    sz_min, sz_max = 1, 99
    xa_min, xa_max = 1, 10  # 15
    ya_min, ya_max = 1, 10  # 15

    def __init__(self, working_zone=tuple, angles=int, rotation=int, size=int, x_amount=int, y_amount=int, depth=False):
        self.working_zone = working_zone
        self.angles = angles
        self.rotation = rotation
        self.size = size
        self.x_amount = x_amount
        self.y_amount = y_amount
        self.depth = depth

    def generate_all_params(self):
        # TODO: Auto-add values by body size
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
        if random() >= 0.5:
            return parent1
        else:
            return parent2

    def generate_working_zone(self):
        x_start = randint(self.x_min, self.x_max - 1)
        x_end = randint(x_start + 1, self.x_max)

        y_start = randint(self.y_min, self.y_max - 1)
        y_end = randint(y_start + 1, self.y_max)

        x_size = x_start, x_end
        y_size = y_start, y_end

        if self.depth:
            z_start = randint(self.z_min, self.z_max - 1)
            z_end = randint(z_start + 1, self.z_max)
            z_size = z_start, z_end
            self.working_zone = (x_size, y_size, z_size)
        else:
            self.working_zone = (x_size, y_size)

    def generate_cells_angles(self):
        self.angles = randint(self.an_min, self.an_max)

    def generate_cells_rotation(self):
        self.rotation = randint(self.rt_min, self.rt_max)

    def generate_cells_size(self):
        self.size = randint(self.sz_min, self.sz_max)

    def generate_cells_amount(self):
        self.x_amount = randint(self.xa_min, self.xa_max)
        self.y_amount = randint(self.ya_min, self.ya_max)

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
        start = self.__mutate_parameter(self.x_min, self.x_max, start)
        stop = self.__mutate_parameter(self.x_min, self.x_max, stop)
        if start == stop:
            return self._mutate_x_size()
        return min(start, stop), max(start, stop)

    def _mutate_y_size(self):
        start, stop = self.working_zone[1]
        start = self.__mutate_parameter(self.y_min, self.y_max, start)
        stop = self.__mutate_parameter(self.y_min, self.y_max, stop)
        if start == stop:
            return self._mutate_y_size()
        return min(start, stop), max(start, stop)

    def _mutate_z_size(self):
        start, stop = self.working_zone[2]
        start = self.__mutate_parameter(self.z_min, self.z_max, start)
        stop = self.__mutate_parameter(self.z_min, self.z_max, stop)
        if start == stop:
            return self._mutate_z_size()
        return min(start, stop), max(start, stop)

    def _mutate_cells_angles(self):
            self.angles = self.__mutate_parameter(self.an_min, self.an_max, self.angles)

    def _mutate_cells_rotation(self):
        self.rotation = self.__mutate_parameter(self.rt_min, self.rt_max, self.rotation)

    def _mutate_cells_size(self):
        self.size = self.__mutate_parameter(self.sz_min, self.sz_max, self.size)

    def _mutate_cells_amount(self):
        self.x_amount = self.__mutate_parameter(self.xa_min, self.xa_max, self.x_amount)
        self.y_amount = self.__mutate_parameter(self.ya_min, self.ya_max, self.y_amount)

    def __mutate_parameter(self, p_min, p_max, parameter):
        mut_value = self.__create_mut_value_for_parameter(p_min, p_max, self.mut_percentage)
        return self.__check_borders(parameter + randint(-mut_value, mut_value), p_min, p_max)

    def __create_mut_value_for_parameter(self, v_min, v_max, per):
        return ceil((v_max - v_min) * per / 100)

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

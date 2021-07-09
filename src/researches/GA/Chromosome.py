from random import randint


class Chromosome:
    working_zone = tuple
    angles = int
    rotation = int
    size = int
    x_amount = int
    y_amount = int

    def generate_all_params(self):
        # TODO: Auto-add values by body size
        self.generate_working_zone()
        self.generate_cells_angles()
        self.generate_cells_rotation()
        self.generate_cells_size()
        self.generate_cells_amount()

    def generate_working_zone(self):
        x_start = randint(0, 250 - 1)
        x_end = x_start + randint(0 + 1, 250 - x_start)

        y_start = randint(0, 250 - 1)
        y_end = y_start + randint(0 + 1, 250 - y_start)

        x_size = x_start, x_end
        y_size = y_start, y_end

        self.working_zone = (x_size, y_size)

    def generate_cells_angles(self):
        # self.angles = randint(3, 8)
        self.angles = randint(3, 5)

    def generate_cells_rotation(self):
        self.rotation = randint(0, 180)

    def generate_cells_size(self):
        self.size = randint(1, 60)

    def generate_cells_amount(self):
        self.x_amount = randint(1, 3)  # 15
        self.y_amount = randint(1, 3)  # 15

    def __str__(self):
        string = \
            f"{self.__repr__()}" \
            f"\nWorking zone: {self.working_zone} " \
            f"\nAngles: {self.angles}" \
            f"\nRotation: {self.rotation}" \
            f"\nSize: {self.size}" \
            f"\nAmount (x, y): {self.x_amount}, {self.y_amount}"
        return string

    # def __init__(self):
    #     self.working_zone = working_zone
    #     self.angles = angles
    #     self.rotation = rotation
    #     self.size = size
    #     self.x_amount = x_amount
    #     self.y_amount = y_amount

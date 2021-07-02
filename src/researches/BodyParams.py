class BodyParameters:
    length = 0
    width = 0
    height = 0
    v = 0

    def __init__(self, x0, x1, y0, y1, z0, z1):
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.length = x1 - x0
        self.width = y1 - y0
        self.height = z1 - z0
        self.v = self.length * self.width * self.height

    def get_x0_body(self):
        return self.x0

    def get_xend_body(self):
        return self.x1

    def get_y0_body(self):
        return self.y0

    def get_yend_body(self):
        return self.y1

    def get_z0_body(self):
        return self.z0

    def get_zend_body(self):
        return self.z1

    def get_x0_cells(self):
        return self.x0

    def get_xend_cells(self):
        return self.x1

    def get_y0_cells(self):
        return self.y0

    def get_yend_cells(self):
        return self.y1

    def get_z0_cells(self):
        return self.z0

    def get_zend_cells(self):
        return self.z1

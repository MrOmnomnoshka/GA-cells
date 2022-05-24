class BodyParameters:
    length = 0
    width = 0
    height = 0
    v = 0

    def __init__(self, x0, x1, y0, y1, z0, z1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.z0 = z0
        self.z1 = z1
        self.length = x1 - x0
        self.width = y1 - y0
        self.height = z1 - z0
        self.area = self.length * self.width
        self.v = self.area * self.height
        
    def make_ox_symmetry(self, mirror):
        y1_s = self.y0 + (mirror - self.y0) * 2
        y0_s = self.y1 + (mirror - self.y1) * 2
        self.y0, self.y1 = y0_s, y1_s
        
    def make_oy_symmetry(self, mirror):
        x1_s = self.x0 + (mirror - self.x0) * 2
        x0_s = self.x1 + (mirror - self.x1) * 2
        self.x0, self.x1 = x0_s, x1_s

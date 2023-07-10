from svgpathtools import svg2paths, Path, Line, QuadraticBezier, CubicBezier, Arc, parse_path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from optimization import Optimization
import glob, os
import clipboard


# AREA_H = 95.
# AREA_W = 140.
# LEFT_MARGIN = 37.0
# RIGHT_MARGIN = 28.0
# BOTTOM_MARGIN = 30.0
# TOP_MARGIN = 40.0

AREA_H = 95.
AREA_W = 140.
LEFT_MARGIN = 10.0
RIGHT_MARGIN = 10.0
BOTTOM_MARGIN = 10.0
TOP_MARGIN = 10.0

HEIGHT = AREA_H - TOP_MARGIN - BOTTOM_MARGIN
WIDTH = AREA_W - LEFT_MARGIN - RIGHT_MARGIN
# MARGIN = 10.0
LANDSCAPE = False

OFFSET = 20.0
SURFACE = 0.0

RESOLUTION = 6
FILE = 'generic_01.svg'


class Reader(object):
    def __init__(self):
        self.file = ''
        self.paths = None
        self.attributes = None
        self.width = 0.0
        self.height = 0.0
        self.ratio = 1.0
        self.targets = 1.0
        self.off_x = 0
        self.off_y = 0
        self.vertical_flip = False
        self.horizontal_flip = False

    def change_file(self, file):
        self.file = file
        self.paths, self.attributes = svg2paths(file)

        xmin, xmax, ymin, ymax = self.find_bbox()
        self.width = xmax - xmin
        self.height = ymax - ymin

        self.ratio = min(WIDTH / self.width, HEIGHT / self.height)

        dim = [WIDTH / self.width, HEIGHT / self.height].index(max([WIDTH / self.width, HEIGHT / self.height]))
        if dim == 0:
            print('Fit the Height')
            self.off_x = -xmin * self.ratio + abs(WIDTH - self.width * self.ratio) / 2
            self.off_y = -ymin * self.ratio

        else:
            print('Fit the Width')
            self.off_x = -xmin * self.ratio
            self.off_y = -ymin * self.ratio + abs(HEIGHT - self.height * self.ratio) / 2

        self.targets = []

    def find_bbox(self):
        bbox = [1e1000, -1e1000, 1e1000, -1e1000]
        for obj in self.paths:
            # for segment in obj:
            xmin, xmax, ymin, ymax = obj.bbox()

            bbox[0] = xmin if xmin < bbox[0] else bbox[0]
            bbox[1] = xmax if xmax > bbox[1] else bbox[1]
            bbox[2] = ymin if ymin < bbox[2] else bbox[2]
            bbox[3] = ymax if ymax > bbox[3] else bbox[3]

        return bbox[0], bbox[1], bbox[2], bbox[3]

    def transform(self, x, y, offs=False):
        # x2 = round(MARGIN + AREA_H - (self.ratio * x - self.off_x), 3) if self.horizontal_flip else round(MARGIN + self.ratio * x + self.off_x, 3)
        # y2 = round(MARGIN + AREA_H - (self.ratio * y - self.off_y), 3) if self.vertical_flip else round(MARGIN + self.ratio * y + self.off_y, 3)
        x2 = round(LEFT_MARGIN + self.ratio * x + self.off_x, 4)
        y2 = round(BOTTOM_MARGIN + self.ratio * y + self.off_y, 4)
        z2 = OFFSET if offs else SURFACE
        result = [x2, round(abs(AREA_H - TOP_MARGIN + BOTTOM_MARGIN - y2), 4), z2]

        if LANDSCAPE:
            result = [result[1], AREA_W - result[0], result[2]]

        return result

    def extract_target(self):
        for obj in self.paths:
            for index, segment in enumerate(obj):
                # print(segment)
                if isinstance(segment, Line):
                    if index == 0:
                        self.targets.append(self.transform(segment.start.real, segment.start.imag, True))
                        self.targets.append(self.transform(segment.start.real, segment.start.imag))

                    if segment.start.real == segment.end.real and segment.start.imag == segment.end.imag:
                        None
                    else:
                        self.targets.append(self.transform(segment.end.real, segment.end.imag))

                    if index == len(obj) - 1:
                        self.targets.append(self.transform(segment.end.real, segment.end.imag, True))

                elif isinstance(segment, CubicBezier) or isinstance(segment, QuadraticBezier):
                    self.targets.append(self.transform(segment.points(0).real, segment.points(0).imag, True))
                    for i in range(0, RESOLUTION + 1, 1):
                        self.targets.append(self.transform(segment.points(i/RESOLUTION).real, segment.points(i/RESOLUTION).imag))

                    if index == len(obj) - 1:
                        self.targets.append(self.transform(segment.points(1).real, segment.points(1).imag, True))

                elif isinstance(segment, Arc):
                    self.targets.append(self.transform(segment.point(0).real, segment.point(0).imag, True))
                    for i in range(0, RESOLUTION + 1, 1):
                        self.targets.append(self.transform(segment.point(i/RESOLUTION).real, segment.point(i/RESOLUTION).imag))

                    if index == len(obj) - 1:
                        self.targets.append(self.transform(segment.point(1).real, segment.point(1).imag, True))
                # print(self.targets)

    def shorten(self):
        targets = self.targets
        print("Before shortening:", len(targets))
        # print("Before shortening:\n", targets)
        for index, target in enumerate(targets):
            if index + 3 >= len(targets):
                break
            if target[0:2] == targets[index + 1][0:2] == targets[index + 2][0:2] == targets[index + 3][0:2]:
                # Endpoint → Pickup → Land → Start at the same coordinate
                # Remove last three
                del targets[index + 1: index + 4]
            elif target[0:2] == targets[index + 1][0:2] == targets[index + 2][0:2]:
                # Endpoint → Pickup → Land → Start at the same coordinate
                # Remove last three
                del targets[index + 1: index + 3]
        self.targets = targets
        print("After shortening:", len(targets))
        # print("After shortening:\n", targets)

    def get_string(self):
        result = ''
        for target in self.targets:
            target = [round(num, 4) for num in target]
            result += str(target) + ";"

        clipboard.copy(result.replace(' ', ''))

        return result.replace(' ', '')

    def get_path(self):
        result = '['
        for idx, target in enumerate(self.targets[:-1]):
            if target[-1] == 0:
                start = [round(num, 4) for num in target[:-1]]
                end = [round(num, 4) for num in self.targets[idx + 1][:-1]]
                result += f"[{start}, {end}]" + ","
        result = result[:-1] + ']'
        clipboard.copy(result.replace(' ', ''))

        return result.replace(' ', '')

    def optimize(self):
        result = list()
        segment = list()
        for idx, target in enumerate(self.targets[:]):
            if target[-1] == SURFACE:
                segment.append(target[:-1])
            elif len(segment) > 0:
                result.append(segment[:])
                segment = list()
        opt_targets = list()
        genetic = Optimization(result, n_pop=1000, power=1, n_iter=100, r_mut=.8, n_cross=1)
        opt_path, score = genetic.run()
        del genetic
        print("Score:", score)
        genetic = Optimization(opt_path, n_pop=1000, power=1, n_iter=100, r_mut=.8, n_cross=3)
        opt_path, score = genetic.run()
        del genetic
        print("Score:", score)
        genetic = Optimization(opt_path, n_pop=1000, power=1, n_iter=100, r_mut=.8, n_cross=6)
        opt_path, score = genetic.run()
        del genetic
        print("Score:", score)
        for idx, seg in enumerate(opt_path):
            opt_targets.append(seg[0] + [OFFSET])
            for target in seg:
                opt_targets.append(target + [SURFACE])
            opt_targets.append(seg[-1] + [OFFSET])
        self.targets = opt_targets

    def canvas(self):
        targets = self.targets
        off = [[0, 0]]

        plt.ion()
        fig, ax = plt.subplots(subplot_kw={'aspect': 'equal'})
        plt.xlim([0, AREA_H] if LANDSCAPE else [0, AREA_W])
        plt.ylim([0, AREA_W] if LANDSCAPE else [0, AREA_H])
        plt.grid(color='grey', linestyle='-', linewidth=0.1)
        plt.title("Drawing")
        plt.xlabel("X-Axis")
        plt.ylabel("Y-Axis")

        ax.add_patch(Rectangle((BOTTOM_MARGIN, RIGHT_MARGIN), HEIGHT, WIDTH, linestyle='-', linewidth=0.2, fill=False) if LANDSCAPE else
                      Rectangle((LEFT_MARGIN, BOTTOM_MARGIN), WIDTH, HEIGHT, linestyle='-', linewidth=0.2, fill=False))
        # offs, = ax.plot(0, 0, 'b--', linewidth=0.3, label="Offsets", marker=".", markersize=1.)
        # plt.show(block=False)
        import os
        os.system('pause')
        while len(targets) > 0:
            drawing, = ax.plot(0, 0, 'r-', linewidth=.8, label="Target")
            on = []
            for index, target in enumerate(targets):
                if target[2] == OFFSET:
                    prev_x, prev_y = off[-1]
                    dist = ((prev_x - target[0]) ** 2 + (prev_y - target[1]) ** 2) ** 0.5
                    off.append((target[0], target[1]))
                    x_off, y_off = zip(*off)
                    if len(x_off) % 2 == 0:
                        ax.plot(x_off[-2:], y_off[-2:], 'b--', linewidth=0.3, label="Offsets", marker=".", markersize=1.)
                    # offs.set_xdata(x_off)
                    # offs.set_ydata(y_off)
                    # fig.canvas.draw()
                    # fig.canvas.flush_events()
                    plt.pause(0.2 + 0.01 * dist)
                    del targets[:index + 1]
                    break
                else:
                    on.append((target[0], target[1]))
                    x_on, y_on = zip(*on)
                    drawing.set_xdata(x_on)
                    drawing.set_ydata(y_on)
                    fig.canvas.draw()
                    plt.pause(0.001)

        print('Finished canvas!')
        plt.ioff()
        plt.show()



if __name__ == '__main__':
    files = []
    for index, file in enumerate(glob.glob(".\drawings\*.svg")):
        print(str(index) + ".", file[10:], end=" ")
        files.append(file)
    choice = int(input("\nChoose one: "))
    # choice = 42
    reader = Reader()
    reader.change_file(files[choice])
    reader.extract_target()
    reader.shorten()
    reader.optimize()
    reader.canvas()




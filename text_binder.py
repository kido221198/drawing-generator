from svgpathtools import svg2paths, Path, Line, QuadraticBezier, CubicBezier, Arc, parse_path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import glob, os
import clipboard
import json
# from irc5_client import tcp_client
from emb60r_client import tcp_client

# AREA_W = 60.0
# AREA_H = 105.0
# MARGIN = 10.0

AREA_H = 95.
AREA_W = 140.
LEFT_MARGIN = 41.0
RIGHT_MARGIN = 24.0
BOTTOM_MARGIN = 25.0
TOP_MARGIN = 45.0
HEIGHT = AREA_H - TOP_MARGIN - BOTTOM_MARGIN
WIDTH = AREA_W - LEFT_MARGIN - RIGHT_MARGIN
LANDSCAPE = True

OFFSET = 20.0
SURFACE = 0.0
GAP = 8.0
SPACE = 3 * GAP

class Binder(object):
    def __init__(self, tcp=False):
        self.file = ''
        self.targets = []
        self.map = {}
        self.off_x = 0.
        self.off_y = 0.
        self.width = 0.0
        self.height = 0.0
        self.text = ""
        self.tcp = tcp_client() if tcp is True else None

    def choose_font(self, font):
        with open(f"./fonts/{font}.json") as fp:
            self.map = json.load(fp)

    def transfer(self):
        print("Targets:", len(self.targets))
        self.tcp.save_targets(1, self.get_string())

    def execute(self):
        self.tcp.execute_targets(1)

    def transform_text(self, text):
        self.text = text
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

        cursor = 0.

        for char in self.text:
            if char in self.map:
                y_off = self.map[char]["size"]["y_offset"]
                for target in self.map[char]["targets"]:
                    self.targets.append(self.transform(target, cursor, y_off))
                cursor += (self.map[char]["size"]["width"] + GAP) * self.ratio
            else:
                cursor += SPACE * self.ratio

    def transform(self, target, cursor, y_off):

        x = round(LEFT_MARGIN + cursor + self.ratio * target[0] + self.off_x, 3)
        y = round(BOTTOM_MARGIN + self.ratio * (target[1] + y_off) + self.off_y, 3)

        result = [x, y, target[2]]

        if LANDSCAPE:
            result = [result[1], round(AREA_W - result[0], 3), result[2]]

        return result

    def find_bbox(self):
        bbox = [0, 0, 1e1000, -1e1000]  # [xmin, xmax, ymin, ymax]
        for char in self.text:
            # for segment in obj:
            if char in self.map:
                bbox[1] += self.map[char]["size"]["width"] + GAP
                self.height = max(self.height, self.map[char]["size"]["height"] + self.map[char]["size"]["y_offset"])
                bbox[2] = min(bbox[2], self.map[char]["size"]["y_offset"])
                bbox[3] = max(bbox[3], self.map[char]["size"]["y_offset"] + self.map[char]["size"]["height"])
            else:
                bbox[1] += SPACE
        print(bbox)
        return bbox[0], bbox[1] - GAP, bbox[2], bbox[3]

    def canvas(self):
        targets = self.targets
        off = []

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
        offs, = ax.plot(0, 0, 'b.', linewidth=1, label="Offsets")
        # plt.show(block=False)

        while len(targets) > 0:
            drawing, = ax.plot(0, 0, 'r-', linewidth=1, label="Target")
            on = []
            for index, target in enumerate(targets):
                if target[2] == OFFSET:
                    off.append((target[0], target[1]))
                    x_off, y_off = zip(*off)
                    offs.set_xdata(x_off)
                    offs.set_ydata(y_off)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    plt.pause(0.0001)
                    del targets[:index + 1]
                    break
                else:
                    on.append((target[0], target[1]))
                    x_on, y_on = zip(*on)
                    drawing.set_xdata(x_on)
                    drawing.set_ydata(y_on)
                    fig.canvas.draw()
                    plt.pause(0.0001)
        print('Finished canvas!')
        plt.ioff()
        plt.show()

    def get_string(self):
        result = ''
        for target in self.targets:
            result += str(target) + ";"

        clipboard.copy(result.replace(' ', ''))

        return result.replace(' ', '')


if __name__ == '__main__':
    binder = Binder()
    while True:
        files = []
        for index, file in enumerate(glob.glob("./fonts/*.json")):
            print(str(index) + ".", file[file.find("fonts") + 6:file.rfind(".json")], end=" ")
            files.append(file[file.find("fonts") + 6:file.rfind(".json")])
        choice = int(input("\nChoose one: "))
        binder.choose_font(files[choice])
        binder.transform_text(input("Input text: "))
        binder.get_string()
        # binder.transfer()
        # binder.execute()
        binder.canvas()







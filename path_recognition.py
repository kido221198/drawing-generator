"""Test the image tracer."""

import matplotlib.pyplot as plt
import clipboard
import glob
import cv2
import time

from svgpathtools import svg2paths, Path, Line, QuadraticBezier, CubicBezier, Arc, parse_path
from matplotlib.patches import Rectangle
from svgtrace import trace
from pathlib import Path
from irc5_client import tcp_client

# WIDTH = 60.
# HEIGHT = 105.
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

THISDIR = str(Path(__file__).resolve().parent)
OFFSET = 20.0
SURFACE = 0.0
RESOLUTION = 3


class ImageExtractor():
    def __init__(self, tcp=False):
        self.file_name = ''
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
        self.scale_percent = 100  # percent of original size
        self.image_type = None
        self.figure = None
        self.ax = None
        self.minimum_gap = 15.
        self.frame_rate = 30
        self.tcp = tcp_client() if tcp is True else None
        # self.tcp = None

    def image_capture(self):
        cam = cv2.VideoCapture(0)
        prev = 0

        if not cam.isOpened():
            raise Exception("Could not open camera/file")

        while True:
            time_elapsed = time.time() - prev

            if time_elapsed > 1. / self.frame_rate:

                ret_val, img = cam.read()
                height, width = img.shape[:2]
                left = int(width * 0.3)
                right = int(width * 0.7)
                top = int(height * 0.01)
                bottom = int(height * 0.51)
                crop_img = img[top:bottom, left:right]

                if not ret_val:
                    cam.set(cv2.CAP_PROP_POS_FRAMES, 0)  # restart video
                    continue
                prev = time.time()

                img = cv2.rectangle(img, (left, top), (right, bottom), (255, 0, 0), 1)
                cv2.imshow('Camera', img)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("1"):
                    ts = int(time.time() * 1000)
                    cv2.imwrite(f'./images/{ts}.jpg', crop_img)
                    self.change_file(str(ts), 'jpg')
                    self.extract_target()
                    self.shorten()
                    continue
                    # self.canvas()
                elif key == ord("2"):
                    self.tcp.save_targets(1, self.get_string())
                    # self.canvas()
                    continue
                elif key == ord("3"):
                    self.tcp.execute_targets(1)
                    continue
                elif key == ord("0"):
                    break


    def change_file(self, file_name, file_type):
        self.file_name = file_name
        self.image_type = file_type
        self.pre_filter()
        self.generate_svg()
        self.paths, self.attributes = svg2paths(f"./drawings/{self.file_name}.svg")
        self.paths = self.paths[1:]

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

        # print("Horizontal flip:", self.horizontal_flip)
        # print("Vertical flip:", self.vertical_flip)
        self.targets = []

    def pre_filter(self):
        print(self.file_name, self.image_type)

        image = cv2.imread(f"./images/{self.file_name}.{self.image_type}")
        width = int(image.shape[1] * self.scale_percent / 100)
        height = int(image.shape[0] * self.scale_percent / 100)
        dim = (width, height)
        resized_img = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        imgray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        retval, thresh = cv2.threshold(imgray, 150, 255, cv2.THRESH_BINARY)
        # blurred = cv2.GaussianBlur(thresh, (3, 3), 0)
        fuzzy_binary = thresh.astype(float) / 255
        black_white = fuzzy_binary.astype(int) * 255

        # self.figure, self.ax = plt.subplots(1, 3, subplot_kw={'aspect': 'equal'})
        # self.ax[0].imshow(image, cmap='gray')
        # self.ax[1].imshow(black_white, cmap='gray')
        # plt.show(block=False)

        cv2.imwrite(f'./images/filtered_{self.file_name}.jpg', black_white)

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

    def generate_svg(self):
        Path(f"./drawings/{self.file_name}.svg").write_text(trace(f"{THISDIR}/images/filtered_{self.file_name}.jpg", True), encoding="utf-8")

    def canvas(self):
        targets = self.targets
        off = []

        plt.ion()
        # fig, ax = plt.subplots(subplot_kw={'aspect': 'equal'})
        plt.xlim([0, AREA_H] if LANDSCAPE else [0, AREA_W])
        plt.ylim([0, AREA_W] if LANDSCAPE else [0, AREA_H])
        self.ax[2].grid(color='grey', linestyle='-', linewidth=0.1)
        self.ax[2].title.set_text("Drawing")
        self.ax[2].set_xlabel("X-Axis")
        self.ax[2].set_ylabel("Y-Axis")

        self.ax[2].add_patch(Rectangle((BOTTOM_MARGIN, RIGHT_MARGIN), HEIGHT, WIDTH, linestyle='-', linewidth=0.2, fill=False) if LANDSCAPE else
                     Rectangle((LEFT_MARGIN, BOTTOM_MARGIN), WIDTH, HEIGHT, linestyle='-', linewidth=0.2, fill=False))
        offs, = self.ax[2].plot(0, 0, 'b.', linewidth=1, label="Offsets")
        # plt.show(block=False)

        while len(targets) > 0:
            drawing, = self.ax[2].plot(0, 0, 'r-', linewidth=0.5, label="Target")
            on = []
            for index, target in enumerate(targets):
                if target[2] == OFFSET:
                    off.append((target[0], target[1]))
                    x_off, y_off = zip(*off)
                    offs.set_xdata(x_off)
                    offs.set_ydata(y_off)
                    self.figure.canvas.draw()
                    self.figure.canvas.flush_events()
                    plt.pause(0.5)
                    del targets[:index + 1]
                    break
                else:
                    on.append((target[0], target[1]))
                    x_on, y_on = zip(*on)
                    drawing.set_xdata(x_on)
                    drawing.set_ydata(y_on)
                    self.figure.canvas.draw()
                    self.figure.canvas.flush_events()
                    plt.pause(0.01)
        print('Finished canvas!')
        plt.ioff()
        plt.show(block=False)

    def transform(self, x, y, offs=False):
        # x2 = round(MARGIN + HEIGHT - (self.ratio * x - self.off_x), 3) if self.horizontal_flip else round(MARGIN + self.ratio * x + self.off_x, 3)
        # y2 = round(MARGIN + HEIGHT - (self.ratio * y - self.off_y), 3) if self.vertical_flip else round(MARGIN + self.ratio * y + self.off_y, 3)
        x2 = round(LEFT_MARGIN + self.ratio * x + self.off_x, 3)
        y2 = round(BOTTOM_MARGIN + self.ratio * y + self.off_y, 3)
        z2 = OFFSET if offs else SURFACE
        result = [x2, round(abs(AREA_H - TOP_MARGIN + BOTTOM_MARGIN - y2)), z2]

        if LANDSCAPE:
            result = [result[1], round(AREA_W - result[0], 3), result[2]]

        return result

    def extract_target(self):
        for obj in self.paths:
            for index, segment in enumerate(obj):
                # print(segment)
                if isinstance(segment, Line):
                    if index == 0:
                        self.targets.append(self.transform(segment.start.real, segment.start.imag, True))
                        self.targets.append(self.transform(segment.start.real, segment.start.imag))

                    target = self.transform(segment.end.real, segment.end.imag)
                    if ((self.targets[-1][0] - target[0]) ** 2 + (self.targets[-1][1] - target[1]) ** 2 > self.minimum_gap ** 2):
                        self.targets.append([self.targets[-1][0], self.targets[-1][1], OFFSET])
                        self.targets.append([target[0], target[1], OFFSET])
                    self.targets.append(target)

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

    def shorten(self):
        targets = self.targets
        print("Before shortening:", len(targets))
        for index, target in enumerate(targets):
            if index + 3 >= len(targets):
                break
            if target[0:2] == targets[index + 1][0:2] == targets[index + 2][0:2] == targets[index + 3][0:2]:
                del targets[index + 1: index + 4]
            elif target[0:2] == targets[index + 1][0:2] == targets[index + 2][0:2]:
                del targets[index + 1: index + 3]
        self.targets = targets
        print("After shortening:", len(targets))

    def get_string(self):
        result = ''
        for target in self.targets:
            result += str(target) + ";"

        clipboard.copy(result.replace(' ', ''))

        return result.replace(' ', '')


if __name__ == '__main__':

    # files = []
    # for index, file in enumerate(glob.glob(".\images\*")):
    #     print(str(index) + ".", file[9:], end=" ")
    #     files.append(file)
    # choice = int(input("\nChoose one: "))
    # file = files[choice]
    # file_name = file[file.find("images") + 7:file.rfind(".")]
    # file_type = file[file.rfind(".") + 1:]
    # print(file_type)
    extractor = ImageExtractor()
    extractor.image_capture()
    # extractor.change_file(file_name, file_type)
    # extractor.extract_target()
    # extractor.shorten()
    # extractor.get_string()
    # extractor.canvas()
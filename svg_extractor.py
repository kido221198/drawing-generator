from svgpathtools import svg2paths, Path, Line, QuadraticBezier, CubicBezier, Arc, parse_path
import glob
import json

OFFSET = 20.0
SURFACE = 0.0
RESOLUTION = 2


class Extractor(object):
    def __init__(self):
        self.file = ''
        self.paths = None
        self.attributes = None
        self.targets = []
        self.vertical_flip = False
        self.horizontal_flip = False
        self.map = {}
        self.x_offset = 0.
        self.y_offset = 0.
        self.underline_chars = ""

    def specify_underline_chars(self, chars):
        self.underline_chars = chars

    def choose_font(self, font):
        for index, file in enumerate(glob.glob(f"./svg/{font}/*.svg")):
            self.change_file(file)
            self.extract_target()
            self.shorten()
            letter = file[file.find(f"{font}") + len(font) + 1:file.rfind(".svg")]
            letter = letter[0].upper() if len(letter) == 2 else letter
            self.map[letter] = {"targets": self.targets,
                                "size": {"width": self.width, "height": self.height, "x_offset": self.x_offset,
                                         "y_offset": self.y_offset}}
        for char in self.underline_chars:
            self.map[char]["size"]["y_offset"] += self.map["a"]["size"]["height"] - self.map[char]["size"]["height"]
        for i in range(0, 100):
            try:
                output_file = f"./fonts/{font}.json" if i == 0 else f"./fonts/{font}_{i}.json"
                with open(output_file, "w") as fp:
                    json.dump(self.map, fp)
                break
            except PermissionError as e:
                i += 1
                continue

    def change_file(self, file):
        self.file = file
        self.paths, self.attributes = svg2paths(file)

        xmin, xmax, ymin, ymax = self.find_bbox()
        self.width = xmax - xmin
        self.height = ymax - ymin
        self.x_offset = xmin
        self.y_offset = ymin
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

        return round(bbox[0], 3), round(bbox[1], 3), round(bbox[2], 3), round(bbox[3], 3)

    def transform(self, x, y, offs=False):
        x2 = round(x, 3)
        y2 = round(y, 3)
        z2 = OFFSET if offs else SURFACE
        return [x2, abs(self.height - y2), z2]

    def extract_target(self):
        # for obj in self.paths:
        obj = self.paths[0]
        for index, segment in enumerate(obj):
            # print(segment)
            if isinstance(segment, Line):
                self.targets.append(self.transform(segment.start.real, segment.start.imag, True))
                self.targets.append(self.transform(segment.start.real, segment.start.imag))
                self.targets.append(self.transform(segment.end.real, segment.end.imag))
                self.targets.append(self.transform(segment.end.real, segment.end.imag, True))

            elif isinstance(segment, CubicBezier) or isinstance(segment, QuadraticBezier):
                self.targets.append(self.transform(segment.points(0).real, segment.points(0).imag, True))
                for i in range(0, RESOLUTION + 1, 1):
                    self.targets.append(
                        self.transform(segment.points(i / RESOLUTION).real, segment.points(i / RESOLUTION).imag))
                self.targets.append(self.transform(segment.points(1).real, segment.points(1).imag, True))

            elif isinstance(segment, Arc):
                self.targets.append(self.transform(segment.point(0).real, segment.point(0).imag, True))
                for i in range(0, RESOLUTION + 1, 1):
                    self.targets.append(
                        self.transform(segment.point(i / RESOLUTION).real, segment.point(i / RESOLUTION).imag))
                self.targets.append(self.transform(segment.point(1).real, segment.point(1).imag, True))

    def shorten(self):
        targets = self.targets
        # print("Before shortening:", len(targets))
        for index, target in enumerate(targets):
            if index + 3 >= len(targets):
                break
            if target[0:2] == targets[index + 1][0:2] == targets[index + 2][0:2] == targets[index + 3][0:2]:
                del targets[index + 1: index + 4]
            elif target[0:2] == targets[index + 1][0:2] == targets[index + 2][0:2]:
                del targets[index + 1: index + 3]
        self.targets = targets


if __name__ == '__main__':
    files = []
    for index, file in enumerate(glob.glob("./svg/*")):
        print(str(index) + ".", file[file.find("svg") + 4:], end=" ")
        files.append(file[file.find("svg") + 4:])
    choice = int(input("\nChoose one: "))
    underline_chars = input("Specify underline characters: ")
    extractor = Extractor()
    extractor.specify_underline_chars(underline_chars)
    extractor.choose_font(files[choice])





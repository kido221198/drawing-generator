import sys
import clipboard
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from math import sqrt
from irc5_client import tcp_client


WIDTH = 60.0
HEIGHT = 105.0
OFFSET = 20.0
SURFACE = 0.0
MARGIN = 10.0

class TabletSampleWindow(QWidget):
    def __init__(self, parent=None):
        super(TabletSampleWindow, self).__init__(parent)
        self.pen_is_down = False
        self.pen_x = 0
        self.pen_y = 0
        self.pen_pressure = 0
        self.text = ""
        # Resizing the sample window to full desktop size:
        frame_rect = app.desktop().frameGeometry()
        width, height = frame_rect.width(), frame_rect.height()
        self.resize(width, height)
        self.move(-9, 0)
        self.setWindowTitle("Tablet Event Handling")
        self.event = None

        self.offset_x = 0.
        self.offset_y = 0.
        self.offset_z = 20.
        self.targets = []
        self.threshold = 0.9

        self.lines = []
        # self.tcp = tcp_client()

        self.undo_button = QPushButton(self)
        self.undo_button.setText("Undo")
        self.undo_button.move(5, 15)
        self.undo_button.clicked.connect(self.undo_action)

        self.clear_button = QPushButton(self)
        self.clear_button.setText("Clear")
        self.clear_button.move(85, 15)
        self.clear_button.clicked.connect(self.clear_drawing)

        self.export_button = QPushButton(self)
        self.export_button.setText("Export")
        self.export_button.move(165, 15)
        self.export_button.clicked.connect(self.export_drawing)

        self.execute_button = QPushButton(self)
        self.execute_button.setText("Execute")
        self.execute_button.move(245, 15)
        self.execute_button.clicked.connect(self.execute)

        self.show()

    def clear_drawing(self):
        self.targets = []
        self.lines = []
        self.update()

    def export_drawing(self):
        bbox = [1e1000, -1e1000, 1e1000, -1e1000]
        for target in self.targets:
            bbox[0] = target[0] if target[0] < bbox[0] else bbox[0]
            bbox[1] = target[0] if target[0] > bbox[1] else bbox[1]
            bbox[2] = target[1] if target[1] < bbox[2] else bbox[2]
            bbox[3] = target[1] if target[1] > bbox[3] else bbox[3]

        width = bbox[1] - bbox[0]
        height = bbox[3] - bbox[2]
        ratio = min(WIDTH / width, HEIGHT / height)
        dim = [WIDTH / width, HEIGHT / height].index(max([WIDTH / width, HEIGHT / height]))

        if dim == 0:
            print('Fit the Height')
            off_x = -bbox[0] * self.ratio + abs(WIDTH - width * ratio) / 2
            off_y = -bbox[2] * ratio

        else:
            print('Fit the Width')
            off_x = -bbox[0] * ratio
            off_y = -bbox[2] * ratio + abs(HEIGHT - height * ratio) / 2


        for target in self.targets:
            target[0] = round(MARGIN + ratio * target[0] + off_x, 3)
            target[1] = round(abs(HEIGHT + 2 * MARGIN - (MARGIN + ratio * target[1] + off_y)), 3)

        for i, target in enumerate(self.targets):
            if i == len(self.targets) - 1:
                break

            if target[0] == self.targets[i + 1][0] and target[1] == self.targets[i + 1][1] \
                and target[2] == 0 and self.targets[i + 1][2] == 0:
                del self.targets[i]

        print("Targets:", len(self.targets))
        self.tcp.save_targets(1, self.get_string())

    def execute(self):
        self.tcp.execute_targets(1)

    def undo_action(self):
        num_target = len(self.targets)
        num_line = len(self.lines)

        # print("Undo", num_target, num_line)
        pickup_point = 0
        middle_point = 0
        for i in range(num_target - 1, -1, -1):
            if self.targets[i][2] == self.offset_z:
                pickup_point += 1
            else:
                middle_point += 1

            if pickup_point == 2:
                # self.targets.pop()
                break

        for i in range(min(num_target, 3)):
            self.targets.pop()
        for i in range(middle_point - 1):
            self.targets.pop()
            self.lines.pop()

        self.update()


    def tabletEvent(self, tabletEvent):
        x = tabletEvent.x()
        y = tabletEvent.y()
        new_coordinate = False

        self.pen_x = x
        self.pen_y = y

        self.event = tabletEvent.type()

        if self.event == QTabletEvent.TabletPress:
            self.pen_is_down = True
            self.text = "TabletPress event"
            self.targets.append([self.pen_x, self.pen_y, self.offset_z])
            self.targets.append([self.pen_x, self.pen_y, 0])
        elif self.event == QTabletEvent.TabletMove:
            self.pen_is_down = True
            self.text = "TabletMove event"
            self.targets.append([self.pen_x, self.pen_y, 0])
            self.lines.append(QLine(self.targets[-2][0], self.targets[-2][1], self.pen_x, self.pen_y))
        elif self.event == QTabletEvent.TabletRelease:
            self.pen_is_down = False
            self.text = "TabletRelease event"
            self.targets.append([self.pen_x, self.pen_y, self.offset_z])
        self.text += " at x={0}, y={1},".format(self.pen_x, self.pen_y)

        if self.pen_is_down:
            self.text += " Pen is down."

        else:
            self.text += " Pen is up."


        # print(self.targets[-1])
        tabletEvent.accept()
        self.update()

    def paintEvent(self, event):
        text = self.text
        i = text.find("\n\n")
        if i >= 0:
            text = text.left(i)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.drawText(self.rect(), Qt.AlignTop | Qt.AlignLeft , text)

        if len(self.lines) > 0:
            pen = QPen(Qt.red, 2)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(pen)
            for line in self.lines:
                painter.drawLine(line)

    def distance_calculate(self, x1, y1, x2, y2):
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def get_string(self):
        result = ''
        for target in self.targets:
            result += str(target) + ";"

        clipboard.copy(result.replace(' ', ''))

        return result.replace(' ', '')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainform = TabletSampleWindow()
    mainform.show()
    app.exec_()
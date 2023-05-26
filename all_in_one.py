import sys
import clipboard
import numpy as np
import time
import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from math import sqrt
from emb60r_client import tcp_client
from text_binder import Binder
from path_recognition import ImageExtractor


AREA_H = 95.
AREA_W = 140.
LEFT_MARGIN = 41.0
RIGHT_MARGIN = 24.0
BOTTOM_MARGIN = 25.0
TOP_MARGIN = 45.0
HEIGHT = AREA_H - TOP_MARGIN - BOTTOM_MARGIN
WIDTH = AREA_W - LEFT_MARGIN - RIGHT_MARGIN
OFFSET = 20.0
SURFACE = 0.0
LANDSCAPE =True


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.frame_rate = 15

    def run(self):
        # capture from webcam
        cap = cv2.VideoCapture(1)
        prev = 0
        while True:
            time_elapsed = time.time() - prev
            if time_elapsed > 1. / self.frame_rate and self._run_flag:
                ret, cv_img = cap.read()

                # ret_val, img = cap.read()
                # height, width = img.shape[:2]
                # left = int(width * 0.3)
                # right = int(width * 0.7)
                # top = int(height * 0.01)
                # bottom = int(height * 0.51)
                # crop_img = img[top:bottom, left:right]

                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # restart video
                    continue
                prev = time.time()

                # img = cv2.rectangle(img, (left, top), (right, bottom), (255, 0, 0), 1)
                # self.change_pixmap_signal.emit(cv_img)

                if ret:
                    self.change_pixmap_signal.emit(cv_img)
            # shut down capture system
            # cap.release()

    def pause(self):
        self._run_flag = False

    def resume(self):
        self._run_flag = True

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class TabletSampleWindow(QWidget):
    def __init__(self, parent=None):
        super(TabletSampleWindow, self).__init__(parent)
        self.center()
        self.setWindowState(Qt.WindowMaximized)
        self.pen_is_down = False
        self.pen_x = 0
        self.pen_y = 0
        self.pen_pressure = 0
        self.text = ""
        # Resizing the sample window to full desktop size:
        # frame_rect = app.desktop().frameGeometry()
        # width, height = frame_rect.width(), frame_rect.height()
        # self.resize(width, height)
        self.move(-9, 0)
        self.setWindowTitle("FASTory DRAW")
        self.event = None

        self.crop_img = None

        self.offset_x = 0.
        self.offset_y = 0.
        self.offset_z = 20.
        self.targets = []
        self.threshold = 0.9

        self.lines = []
        self.binder = Binder()
        self.binder.choose_font('roboto_small')
        self.image_extractor = ImageExtractor()
        self.tcp = tcp_client()

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        # self.thread.start()
        self.thread.pause()

        # self.window_width = self.frameGeometry().width()
        # self.window_height = self.frameGeometry().height()
        # self.window_width = 1920
        # self.window_height = 1050
        self.setFixedWidth(self.window_width)
        self.setFixedHeight(self.window_height)
        print("Window size:", self.window_width, self.window_height)

        self.bottom_margin = round(0.025 * self.window_height)
        self.top_margin = round(0.025 * self.window_height)
        self.left_margin = round(0.025 * self.window_width)
        self.right_margin = round(0.025 * self.window_width)

        self.space_rows = round(self.window_height * 0.002)
        self.space_columns = round(self.window_width * 0.005)

        self.logo_height = round(self.window_height * 0.08)
        self.logo_width = round(self.window_width * 0.2)
        self.logo_pose = round((self.window_width - self.logo_width) / 2)
        self.preference_height = round(self.window_width * 0.01)
        self.preference_label_width = round(self.window_width * 0.1)
        self.draw_button_width = round(self.window_width * 0.05)
        self.type_button_width = round(self.window_width * 0.05)
        self.capture_button_width = round(self.window_width * 0.05)
        self.undo_button_width = round(self.window_width * 0.05)
        self.clear_button_width = round(self.window_width * 0.05)
        self.generate_button_width = round(self.window_width * 0.05)
        self.execute_button_width = round(self.window_width * 0.05)

        self.first_row = self.top_margin
        self.second_row = self.first_row + self.logo_height + self.space_rows
        self.third_row = self.second_row + self.preference_height + self.space_rows
        self.first_column = self.left_margin
        self.second_column = self.first_column + self.preference_label_width + self.space_columns
        self.third_column = self.second_column + self.draw_button_width + self.space_columns
        self.forth_column = self.third_column + self.type_button_width + self.space_columns
        self.fifth_column = self.forth_column + self.capture_button_width + self.space_columns

        self.ninth_column = self.window_width - self.right_margin - self.execute_button_width
        self.eighth_column = self.ninth_column - self.space_columns - self.generate_button_width
        self.seventh_column = self.eighth_column - self.space_columns - self.clear_button_width
        self.sixth_column = self.seventh_column - self.space_columns - self.undo_button_width

        self.logo = QLabel("FAST-Lab.", self)
        self.logo.setFont(QFont('Arial', 62))
        self.logo.setStyleSheet("QLabel { color : #441587; }")
        self.logo.setGeometry(self.logo_pose, self.first_row, self.logo_width, self.logo_height)

        self.preference_font_size = 12

        self.preference_label = QLabel("Select your preference:", self)
        self.preference_label.setFont(QFont('Arial', self.preference_font_size))
        self.preference_label.setGeometry(self.first_column, self.second_row, self.preference_label_width, self.preference_height)

        self.draw_button = QRadioButton("Draw", self)
        self.draw_button.setFont(QFont('Arial', self.preference_font_size))
        self.draw_button.setGeometry(self.second_column, self.second_row, self.draw_button_width, self.preference_height)
        self.draw_button.toggled.connect(self.switch_mode)

        self.type_button = QRadioButton("Type", self)
        self.type_button.setFont(QFont('Arial', self.preference_font_size))
        self.type_button.setGeometry(self.third_column, self.second_row, self.type_button_width, self.preference_height)
        self.type_button.toggled.connect(self.switch_mode)

        self.camera_button = QRadioButton("Camera", self)
        self.camera_button.setFont(QFont('Arial', self.preference_font_size))
        self.camera_button.setGeometry(self.forth_column, self.second_row, self.capture_button_width, self.preference_height)
        self.camera_button.toggled.connect(self.switch_mode)

        self.undo_button = QPushButton(self)
        self.undo_button.setText("Undo")
        self.undo_button.setGeometry(self.sixth_column, self.second_row, self.undo_button_width, self.preference_height)
        self.undo_button.clicked.connect(self.undo_action)
        self.undo_button.hide()

        self.clear_button = QPushButton(self)
        self.clear_button.setText("Clear")
        self.clear_button.setGeometry(self.seventh_column, self.second_row, self.clear_button_width, self.preference_height)
        self.clear_button.clicked.connect(self.clear_drawing)
        self.clear_button.hide()

        self.generate_button = QPushButton(self)
        self.generate_button.setText("Generate")
        self.generate_button.setGeometry(self.eighth_column, self.second_row, self.generate_button_width, self.preference_height)
        self.generate_button.clicked.connect(self.export_drawing)
        self.generate_button.hide()

        self.execute_button = QPushButton(self)
        self.execute_button.setText("Execute")
        self.execute_button.setGeometry(self.ninth_column, self.second_row, self.execute_button_width, self.preference_height)
        self.execute_button.clicked.connect(self.execute)
        self.execute_button.hide()

        self.interact_area_width = self.window_width - self.left_margin - self.right_margin
        self.interact_area_height = self.window_height - self.bottom_margin * 2 - self.third_row
        self.interact_area = QGraphicsView(self)
        self.interact_area.setGeometry(self.first_column, self.third_row, self.interact_area_width, self.interact_area_height)
        # self.white_board = QGraphicsScene(self.interact_area)
        self.interact_area.setStyleSheet("background: transparent");
        # self.interact_area.setScene(self.white_board)
        # self.white_board.setSceneRect(0, 0, self.interact_area_width - 2, self.interact_area_height - 2)
        self.interact_area.hide()

        self.type_box_height = round(self.window_height * 0.1)
        self.type_box_width = round(self.window_width * 0.6)
        self.type_box_top = round((self.window_height - self.type_box_height) / 2)
        self.type_box_left = round((self.window_width - self.type_box_width) / 2)
        self.type_box = QLineEdit(self)
        self.type_box.setAlignment(Qt.AlignCenter)
        self.type_box.setGeometry(self.type_box_left, self.type_box_top, self.type_box_width, self.type_box_height)
        self.type_box.setFont(QFont('Arial', self.preference_font_size * 2))
        self.type_box.hide()

        self.image_view_width = self.window_width - self.left_margin - self.right_margin
        self.image_view_height = self.window_height - self.bottom_margin * 2 - self.third_row
        self.image_view = QLabel(self)
        self.image_view.setAlignment(Qt.AlignCenter)
        self.image_view.setGeometry(self.first_column, self.third_row, self.image_view_width, self.image_view_height)
        self.image_view.hide()

        self.show()

    def center(self):
        frameGm = self.frameGeometry()
        # screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        screen = app.primaryScreen()
        # centerPoint = QApplication.desktop().screenGeometry(screen).center()
        centerPoint = screen.geometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
        rect = screen.availableGeometry()
        # rect =QApplication.desktop().screenGeometry(screen)
        self.window_width = rect.width()
        self.window_height = rect.height()

        # print('Available: %d x %d' % (rect.width(), rect.height()))

    def switch_mode(self):
        if self.camera_button.isChecked():
            self.camera_mode_selected()
        elif self.draw_button.isChecked():
            self.draw_mode_selected()
        elif self.type_button.isChecked():
            self.type_mode_selected()

    def camera_mode_selected(self):
        self.undo_button.hide() if not self.undo_button.isHidden() else None
        self.generate_button.hide() if not self.clear_button.isHidden() else None
        self.generate_button.show() if self.generate_button.isHidden() else None
        self.execute_button.show() if self.execute_button.isHidden() else None
        self.type_box.hide() if not self.type_box.isHidden() else None
        self.image_view.show() if self.image_view.isHidden() else None
        self.interact_area.hide() if not self.interact_area.isHidden() else None
        self.clear_drawing()
        self.thread.resume()

    def draw_mode_selected(self):
        self.undo_button.show() if self.undo_button.isHidden() else None
        self.clear_button.show() if self.clear_button.isHidden() else None
        self.generate_button.show() if self.generate_button.isHidden() else None
        self.execute_button.show() if self.execute_button.isHidden() else None
        self.type_box.hide() if not self.type_box.isHidden() else None
        self.image_view.hide() if not self.image_view.isHidden() else None
        self.interact_area.show() if self.interact_area.isHidden() else None
        self.clear_drawing()
        self.thread.pause()

    def type_mode_selected(self):
        self.undo_button.hide() if not self.undo_button.isHidden() else None
        self.clear_button.hide() if not self.clear_button.isHidden() else None
        self.generate_button.show() if self.generate_button.isHidden() else None
        self.execute_button.show() if self.execute_button.isHidden() else None
        self.type_box.show() if self.type_box.isHidden() else None
        self.image_view.hide() if not self.image_view.isHidden() else None
        self.interact_area.hide() if not self.interact_area.isHidden() else None
        self.clear_drawing()
        self.thread.pause()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        height, width = cv_img.shape[:2]
        left = int(width * 0.3)
        right = int(width * 0.7)
        top = int(height * 0.01)
        bottom = int(height * 0.51)
        self.crop_img = cv_img[top:bottom, left:right]
        cv_img = cv2.rectangle(cv_img, (left, top), (right, bottom), (255, 0, 0), 1)
        qt_img = self.convert_cv_qt(cv_img)
        self.image_view.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.image_view_width, self.image_view_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def clear_drawing(self):
        self.targets = []
        self.lines = []
        self.update()

    def export_drawing(self):
        if self.draw_button.isChecked():
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
                off_x = -bbox[0] * ratio + abs(WIDTH - width * ratio) / 2
                off_y = -bbox[2] * ratio

            else:
                print('Fit the Width')
                off_x = -bbox[0] * ratio
                off_y = -bbox[2] * ratio + abs(HEIGHT - height * ratio) / 2


            for i, target in enumerate(self.targets):
                target[0] = round(LEFT_MARGIN + ratio * target[0] + off_x, 3)
                target[1] = round(BOTTOM_MARGIN + ratio * target[1] + off_y, 3)
                target = [target[0], round(abs(AREA_H - TOP_MARGIN + BOTTOM_MARGIN - target[1]), 3), target[2]]
                if LANDSCAPE:
                    target = [target[1], round(AREA_W - target[0], 3), target[2]]
                self.targets[i] = target

            for i, target in enumerate(self.targets):
                if i == len(self.targets) - 1:
                    break

                if target[0] == self.targets[i + 1][0] and target[1] == self.targets[i + 1][1] \
                    and target[2] == 0 and self.targets[i + 1][2] == 0:
                    del self.targets[i]

            print("Targets:", len(self.targets))
            self.tcp.save_targets(1, self.get_string())

        elif self.type_button.isChecked():
            text = self.type_box.text()
            if len(text) > 0:
                self.binder.transform_text(text)
                # msg = self.binder.get_string()
                # self.tcp.save_targets(1, msg)
                self.tcp.save_targets(1, self.binder.get_string())

        elif self.camera_button.isChecked():
            ts = int(time.time() * 1000)
            cv2.imwrite(f'./images/{ts}.jpg', self.crop_img)
            self.image_extractor.change_file(str(ts), 'jpg')
            self.image_extractor.extract_target()
            self.image_extractor.shorten()
            self.tcp.save_targets(1, self.image_extractor.get_string())

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
        # text = self.text
        # i = text.find("\n\n")
        # if i >= 0:
        #     text = text.left(i)
        # painter = QPainter(self)
        # painter.setRenderHint(QPainter.TextAntialiasing)
        # painter.drawText(self.rect(), Qt.AlignTop | Qt.AlignLeft , text)

        # if len(self.lines) > 0:
        #     pen = QPen(Qt.red, 2)
        #     painter.setRenderHint(QPainter.Antialiasing)
        #     painter.setPen(pen)
        #     for line in self.lines:
        #         painter.drawLine(line)

        self.post_paint_event()

    def post_paint_event(self):
        painter = QPainter(self)

        if len(self.lines) > 0:
            pen = QPen(Qt.red, 2)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(pen)
            for line in self.lines:
                painter.drawLine(line)
        # if len(self.lines) > 0:
            # self.white_board.clear()
            # pen = QPen(Qt.red, 2)
            # for line in self.lines:
            #     item = QGraphicsLineItem(QLineF(line))
            #     item.setPen(QPen(QColor("red")))
            #     # item.setRenderHint(QPainter.Antialiasing)
            #     item.setPen(pen)

                # self.white_board.addItem(item)

            # item = QGraphicsLineItem(QLineF(self.lines[-1]))
            # item.setPen(QPen(QColor("red")))
            # self.white_board.addItem(item)


    def distance_calculate(self, x1, y1, x2, y2):
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def get_string(self):
        result = ''
        for target in self.targets:
            result += str(target) + ";"

        clipboard.copy(result.replace(' ', ''))

        return result.replace(' ', '')

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    print('Screen: %s' % screen.name())
    size = screen.size()
    print('Size: %d x %d' % (size.width(), size.height()))
    rect = screen.availableGeometry()
    print('Available: %d x %d' % (rect.width(), rect.height()))
    mainform = TabletSampleWindow()
    # mainform.showMaximized()
    app.exec_()
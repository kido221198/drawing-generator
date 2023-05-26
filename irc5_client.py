# echo-client.py
import socket
import threading
import time

HOST = "192.168.125.1"  # The server's hostname or IP address
PORT = 5000  # The port used by the server
ACTIONS = {"Save": "01",
           "Execute": "03",
           "Read": "02",
           "Delete": "04",
           "SpeedConfig": "11",
           "NewDrawingSlot": "12",
           "ChangeOrigin": "13"}

TIME_SLEEP = 0.1


class tcp_client(object):
    def __init__(self, host=HOST, port=PORT):
        self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_.connect((host, port))
        self.last_msg_ = ""
        self.response_ = None
        self.received_target_ = None
        self.listen_thread_ = threading.Thread(target=self.listener)
        self.listen_thread_.start()

    def talker_(self, msg):
        self.socket_.send(bytes(msg, 'UTF-8'))

        while self.response_ is None:
            time.sleep(0.2)

        data = self.response_
        self.response_ = None
        return data

    def listener(self):
        while True:
            data = self.socket_.recv(1024).decode("ascii")
            if len(data) > 0:
                self.last_msg_ = data
                if data[0:2] == "03":
                    print("\nOrder " + data[2:] + " complete!\n")
                elif ";" in self.last_msg_:
                    self.received_target_ = self.last_msg_
                else:
                    self.response_ = data

            # time.sleep(0.1)

    def save_targets(self, id, targets):
        err = self.talker_(ACTIONS["Save"] + str(id).zfill(3))
        # Success acknowledgement
        if err == "00":
            targets = [e + ";" for e in targets.split(";") if e]
            targets[0] = "@" + targets[0]  # begin symbol
            targets[-1] = targets[-1] + "#"  # end symbol

            for index, target in enumerate(targets):
                self.socket_.send(bytes(target, 'UTF-8'))
                err = self.response_
                time.sleep(TIME_SLEEP)

                if err == "01":
                    return 1, "Robot error during transmission"

            return 0, "Success"

        # Fail acknowledgement
        elif err == "02":
            return 2, "Robot is busy"

        elif err == "01":
            return 1, "Robot error before transmission"

        else:
            return 1, "Unexpected behavior"

    def read_targets(self, id):
        drawing = ""
        self.socket_.send(ACTIONS["Read"] + str(id).zfill(3))

        while "#" not in drawing:
            if self.received_target_ is not None:
                data = self.received_target_
                self.received_target_ = None

                drawing = drawing + data

                if "#" in data:
                    self.socket_.send(bytes("00", 'UTF-8'))
                    drawing = drawing[drawing.index("@") + 1:drawing.index("#")]

                elif self.last_msg_ == "01":
                    return 1, "Robot error during transmission", None

                elif self.last_msg_ == "02":
                    return 2, "Robot is busy with drawing " + str(id), None

                else:
                    return 1, "Unexpected behavior", None

        return 0, "Success", drawing.split(";")

    def execute_targets(self, id):
        err = self.talker_(ACTIONS["Execute"] + str(id).zfill(3))

        if err == "00":
            return 0, "Success"

        elif err == "02":
            return 2, "Robot is busy with drawing " + str(id)

        elif err == "01":
            return 1, "Robot error"

        else:
            return 1, "Unexpected behavior"

    def delete_targets(self, id):
        err = self.talker_(ACTIONS["Delete"] + str(id).zfill(3))

        if err == "00":
            return 0, "Success"

        elif err == "02":
            return 2, "Robot is busy with drawing " + str(id)

        elif err == "01":
            return 1, "Robot error"

        else:
            return 1, "Unexpected behavior"

    def speed_configure(self, inputs):
        err = self.talker_(ACTIONS["SpeedConfig"] + str(inputs))

        if err == "00":
            return 0, "Success"

        else:
            return 1, "Unexpected behavior"

    def change_origin(self, inputs):
        err = self.talker_(ACTIONS["ChangeOrigin"])
        print(err)
        if err == "00":
            target = f'[{inputs[0]},{inputs[1]},{inputs[2]}]'
            self.socket_.send(bytes(target, 'UTF-8'))

            if err == "00":
                return 0, "Success"

            if err == "01":
                return 1, "Robot error during transmission"

        else:
            return 1, "Unexpected behavior"

    def new_slot(self):
        err = self.talker_(ACTIONS["NewDrawingSlot"])

        if err == "00":
            return 0, "Success"

        else:
            return 1, "Unexpected behavior"

def main():
    client = tcp_client(HOST, PORT)


if __name__ == "__main__":
    main()

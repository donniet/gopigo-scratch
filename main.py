import time
import BaseHTTPServer
import thread
import threading

try:
    import gopigo
except ImportError:
    class gopigo(object):
        @staticmethod
        def us_dist(pin):
            return 100

        @staticmethod
        def volt():
            return 11.5

        @staticmethod
        def fw_ver():
            return "1.7"

        @staticmethod
        def digitalRead(pin):
            return 0

        @staticmethod
        def digitalWrite(pin, val):
            pass

        @staticmethod
        def trim_read():
            return 100

        @staticmethod
        def trim_write(val):
            pass

        @staticmethod
        def enc_tgt(left, right, amount):
            pass

        @staticmethod
        def stop():
            pass

        @staticmethod
        def set_left_speed(val):
            pass

        @staticmethod
        def set_right_speed(val):
            pass

        @staticmethod
        def set_speed(val):
            pass

        @staticmethod
        def servo(val):
            pass

        @staticmethod
        def analogWrite(pin, val):
            pass

        @staticmethod
        def enable_encoders():
            pass

        @staticmethod
        def disable_encoders():
            pass

        @staticmethod
        def right():
            pass

        @staticmethod
        def left():
            pass

        @staticmethod
        def fwd():
            pass

        @staticmethod
        def read_status():
            return [0, 0]


HOST_NAME = ""
PORT_NUMBER = 8080

buzzer_pin = 10
ledl_pin = 17
ledr_pin = 16
usdist_pin = 15
waitingOn = None

DPR = 360.0/64
WHEEL_RAD = 3.25
CHASS_WID = 13.5


class Robot:
    us_dist = 0
    volts = 0.0
    fw_ver = "0.0"
    ledl = 0
    ledr = 0
    trim = 0
    left_speed = 75
    right_speed = 75
    enc_status = 0
    beep_volume = 20
    beep_time = 0.2

    commandVar = threading.Condition()
    mythread = None
    waitingOn = None
    command = None
    done = False

    def start_thread(self):
        self.mythread = thread.start_new_thread(self.loop, self)

    def send_command(self, command):
        self.commandVar.acquire()
        self.command = command
        self.commandVar.notify()
        self.commandVar.release()

    def loop(self):
        while True:
            self.commandVar.acquire()
            while not self.Done and self.command is None:
                self.commandVar.wait()

            if self.Done:
                self.commandVar.release()
                break

            self.process_command(self.command)
            self.command = None
            self.commandVar.release()

    def kill(self):
        self.commandVar.acquire()
        self.Done = True
        self.commandVar.notify()
        self.commandVar.release()
        self.mythread.join()

    def process_command(self, command):
        parts = command.split("/")

        if parts[1] == "poll":
            self.us_dist = gopigo.us_dist(usdist_pin)
            self.enc_status = gopigo.read_status()[0]
            self.volt = gopigo.volt()
            self.fw_ver = gopigo.fw_ver()
            self.trim = gopigo.trim_read() - 100

            if enc_status == 0:
                self.waitingOn = None
        elif parts[1] == "stop":
            gopigo.stop()
        elif parts[1] == "trim_write":
            gopigo.trim_write(int(parts[2]))
        elif parts[1] == "trim_read":
            self.trim = gopigo.trim_read() - 100
        elif parts[1] == "set_speed":
            if parts[2] == "left":
                self.left_speed = int(parts[3])
            elif parts[2] == "right":
                self.right_speed = int(parts[3])
            else:
                self.right_speed = int(parts[3])
                self.left_speed = int(parts[3])
            gopigo.set_left_speed(self.left_speed)
            gopigo.set_right_speed(self.right_speed)
        elif parts[1] == "leds":
            val = 0
            if parts[3] == "on":
                val = 1
            elif parts[3] == "off":
                val = 0
            elif parts[3] == "toggle":
                val = -1

            if parts[2] == "right" or parts[2] == "both":
                if val >= 0:
                    self.ledr = val
                else:
                    self.ledr = 1 - self.ledr

            if parts[2] == "left" or parts[2] == "both":
                if val >= 0:
                    self.ledl = val
                else:
                    self.ledl = 1 - self.ledl

            gopigo.digitalWrite(ledr_pin, self.ledr)
            gopigo.digitalWrite(ledl_pin, self.ledl)
        elif parts[1] == "servo":
            gopigo.servo(int(parts[2]))
        elif parts[1] == "turn":
            self.waitingOn = parts[2]
            direction = parts[3]
            amount = int(parts[4])
            encleft = 0 if direction == "left" else 1
            encright = 1 if direction == "left" else 0
            gopigo.enable_encoders()
            gopigo.enc_tgt(encleft, encright, int(amount / DPR))
            if direction == "left":
                gopigo.left()
            else:
                gopigo.right()
        elif parts[1] == "move":
            self.waitingOn = int(parts[2])
            direction = parts[3]
            amount = int(parts[4])
            gopigo.enable_encoders()
            gopigo.enc_tgt(1, 1, amount)
            if direction == "backward":
                gopigo.bwd()
            else:
                gopigo.fwd()
        elif parts[1] == "beep":
            gopigo.analogWrite(buzzer_pin, self.beep_volume)
            time.sleep(self.beep_time)
            gopigo.analogWrite(buzzer_pin, 0)
        elif parts[1] == "reset_all":
            self.ledl = 0
            self.ledr = 0

            gopigo.digitalWrite(ledl_pin, self.ledl)
            gopigo.digitalWrite(ledr_pin, self.ledr)
            gopigo.analogWrite(buzzer_pin, 0)
#           gopigo.servo(90)
            gopigo.stop()


class GoPiGoServer(BaseHTTPServer.HTTPServer):
    robot = Robot()


class GoPiGoHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        s.server.robot.send_command(s.path)
        s.send_response(200)
        s.send_header("Content-Type", "text/plain")
        s.end_headers()

        if s.path == "/poll":
            s.server.robot.commandVar.acquire()
            if s.server.robot.waitingOn is not None:
                s.wfile.write("_busy %s\n" % s.server.robot.waitingOn)
            else:
                s.wfile.write("volt %s\n" % s.server.robot.volts)
                s.wfile.write("firmware %s\n" % s.server.robot.fw_ver)
                s.wfile.write("led/left %s\n" % "on" if s.server.robot.ledl != 0 else "off")
                s.wfile.write("led/right %s\n" % "on" if s.server.robot.ledr != 0 else "off")
                s.wfile.write("trim %s\n" % s.server.robot.trim)
                s.wfile.write("us_dist %s\n" % s.server.robot.us_dist)
            s.server.robot.commandVar.release()

if __name__ == "__main__":
    httpd = GoPiGoServer((HOST_NAME, PORT_NUMBER), GoPiGoHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

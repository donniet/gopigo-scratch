import time
import gopigo
import BaseHTTPServer

HOST_NAME = ""
PORT_NUMBER = 8080

buzzer_pin = 10
ledl_pin = 17
ledr_pin = 16
waitingOn = None


class GoPiGoServer(BaseHTTPServer.HTTPServer):
    waitingOn = None


class GoPiGoHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        if s.path == "/poll":
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            if s.server.waitingOn is not None:
                s.wfile.write("_busy %s\n", s.server.waitingOn)
            else:
                s.wfile.write("volt %s\n" % gopigo.volt())
                s.wfile.write("firmware %s\n" % gopigo.fw_ver())
                ledl = gopigo.digitalRead(ledl_pin)
                ledr = gopigo.digitalRead(ledr_pin)
                s.wfile.write("led/left %s\n" % "on" if ledl != 0 else "off")
                s.wfile.write("led/right %s\n" % "on" if ledr != 0 else "off")
        elif s.path.startswith("/leds"):
            parts = s.path.split("/")
            pin = ledl_pin
            val = 0
            if parts[2] == "right":
                pin = ledr_pin
            if parts[3] == "on":
                val = 1
            gopigo.digitalWrite(pin, val)
            s.send_response(200)
        elif s.path.startswith("/move_forward/"):
            if s.server.waitingOn is not None:
                s.send_error(400, "waiting on %s" % s.server.waitingOn)
            else:
                parts = s.path.split("/")
                s.server.waitingOn = int(parts[2])
                amount = int(parts[3])
                gopigo.enable_encoders()
                gopigo.enc_tgt(1, 1, amount)
                gopigo.fwd()
                while gopigo.read_status()[0] != 0:
                    time.sleep(0.05)
                s.server.waitingOn = None
                s.send_response(200)
        elif s.path.startswith("/move_backward/"):
            if s.server.waitingOn is not None:
                s.send_error(400, "waiting on %s" % s.server.waitingOn)
            else:
                parts = s.path.split("/")
                s.server.waitingOn = int(parts[2])
                amount = int(parts[3])
                gopigo.enable_encoders()
                gopigo.enc_tgt(1, 1, amount)
                gopigo.bwd()
                while gopigo.read_status()[0] != 0:
                    time.sleep(0.05)
                s.server.waitingOn = None
                s.send_response(200)
        elif s.path == "/beep":
            gopigo.analogWrite(buzzer_pin, 20)
            time.sleep(0.2)
            gopigo.analogWrite(buzzer_pin, 0)
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            s.wfile.write("")
        elif s.path == "/reset_all":
            gopigo.digitalWrite(ledl_pin, 0)
            gopigo.digitalWrite(ledr_pin, 0)
            gopigo.analogWrite(buzzer_pin, 0)
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            s.wfile.write("")
        else:
            s.send_error(404, "Unknown path %s" % s.path)

if __name__ == "__main__":
    httpd = GoPiGoServer((HOST_NAME, PORT_NUMBER), GoPiGoHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

import time
import gopigo
import BaseHTTPServer

HOST_NAME = ""
PORT_NUMBER = 8080

buzzer_pin = 10

class GoPiGoHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        if s.path == "/poll":
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            s.wfile.write("volt %s\n" % gopigo.volt())
            s.wfile.write("firmware %s\n" % gopigo.fw_ver())
        elif s.path == "/beep":
            gopigo.analogWrite(buzzer_pin, 20)
            time.sleep(0.2)
            gopigo.analogWrite(buzzer_pin, 0)
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            s.wfile.write("")
        elif s.path == "/reset_all":
            gopigo.analogWrite(buzzer_pin, 0)
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            s.wfile.write("")
        else:
            s.send_error(404, "Unknown path %s" % s.path)

if __name__ == "__main__":
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), GoPiGoHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

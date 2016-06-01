import time
import gopigo
import BaseHTTPServer

HOST_NAME = ""
PORT_NUMBER = 8080


class GoPiGoHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        if s.path == "/poll":
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
            s.wfile.write("volt %s\n" % gopigo.volt())
            s.wfile.write("firmware %s\n" % gopigo.fw_ver())
        elif s.path == "/beep":
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
        elif s.path == "/reset_all":
            s.send_response(200)
            s.send_header("Content-Type", "text/plain")
            s.end_headers()
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

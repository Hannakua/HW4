from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
import threading
import json
import datetime


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        print(data_dict)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def simple_client_socket(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while True:
            try:
                s.connect((host, port))
                data = s.recv(1024)
                print(f"From server received: {data}")
                s.send(data.encode())
            except ConnectionRefusedError:
                print("Some error, destroy server")
                break


def simple_socket_server(host, port):
    dict_ = {}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        conn, addr = s.accept()
        print(f"Connected by {addr}")
        with conn:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                data_dict = json.loads(data)
                dict_.update({datetime.now(): data_dict})
                print(f"Received message from client: {data}")
                try:
                    with open("storage/data.json", "w") as file:
                        json.dump(dict_, file)
                except Exception as er:
                    print(er)
                conn.send(data.encode())
            conn.close()


if __name__ == "__main__":
    host = socket.gethostname()
    # host = "localhost"
    port = 5000
    server_http = threading.Thread(target=run)
    server_ = threading.Thread(target=simple_socket_server, args=(host, port))
    client_ = threading.Thread(target=simple_client_socket, args=(host, port))

    server_http.start()
    server_.start()
    client_.start()

    server_http.join()
    server_.join()
    client_.join()

    print("Done!")

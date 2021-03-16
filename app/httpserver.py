import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import ssl
import subprocess
from subprocess import TimeoutExpired


class Server(BaseHTTPRequestHandler):
    
    def _set_response(self, message: str, status_code=200):
        self.send_response(code=status_code)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf8"))

    def run_cmd(self, cmd: str, timeout: int):
        proc = subprocess.Popen([cmd], shell=True)
        try:
            proc.communicate(timeout=timeout)
        except TimeoutExpired:
            proc.kill()
            return 0
        except:
            proc.kill()
            return -1

    def _run_cmd(self, cmd: str, timeout: int):
        proc = subprocess.Popen([cmd], shell=True)
        try:
            outs, errs = proc.communicate(timeout=timeout)
            print(f"outs: {outs}")
            print(f"errs: {errs}")
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            print(f"timeout-outs: {outs}")
            print(f"timeout-errs: {errs}")
            return 0
        except:
            proc.kill()
            outs, errs = proc.communicate()
            print(f"other-outs: {outs}")
            print(f"other-errs: {errs}")
            return -1

    def do_GET(self):
        self._set_response(message="success", status_code=200)
        
    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")
        # self._set_headers()
        # self.wfile.write(post_data.encode("utf8"))
        data = json.loads(post_data)
        driver_phone_number = data.get("driver_phone_number")
        rider_phone_number = data.get("rider_phone_number")
        rider_id = data.get("rider_id")
        pickup_address = data.get("pickup_address")
        dropoff_address = data.get("dropoff_address")

        rider_cmd = f'''
            (echo logout
            sleep 4
            echo login
            sleep 2
            echo "\n"
            sleep 2
            echo {rider_phone_number}
            sleep 2
            echo 'request-ride --pickup-address \"{pickup_address}\" --drop-off-address \"{dropoff_address}\"'
            sleep 2
            echo "\n"
            ) | rider-cli
        '''

        driver_cmd = f'''
            (echo logout
            sleep 4
            echo login
            sleep 2
            echo "\n"
            sleep 2
            echo {driver_phone_number}
            sleep 2
            echo 'set-default-location --address \"{pickup_address}\"'
            sleep 2
            echo 'start-pickup-passengers'
            sleep 2
            echo "{rider_id}"
            sleep 2
            echo "\n"
            ) | driver-cli
        '''
        rider_retry = 0
        while rider_retry < 5:
            rider_return_code = self.run_cmd(rider_cmd, timeout=30)
            if rider_return_code == 0:
                driver_retry = 0
                while driver_retry < 5:
                    driver_return_code = self.run_cmd(driver_cmd, timeout=20)
                    if driver_return_code == 0:
                        self._set_response(status_code=200, message="both driver and rider cli succeed!")
                        return
                    else:
                        driver_retry += 1
                if driver_retry == 5:
                    self._set_response(status_code=500, message="rider succeed, but driver failed after 5 tries")
                    return
                self._set_response(status_code=200, message="rider succeed")
            else:
                rider_retry += 1
        self._set_response(status_code=500, message="rider failed after 5 tries, has not tried driver cli yet")
        return
        
def run(server_class=HTTPServer, handler_class=Server, addr="localhost", port=9000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    httpd.socket = ssl.wrap_socket (httpd.socket,
        keyfile="/Users/echowu/Desktop/key.pem",
        certfile='/Users/echowu/Desktop/cert.pem', server_side=True)

    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=9000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
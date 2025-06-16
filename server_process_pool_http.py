import socket
import logging
import multiprocessing
import os
from http import HttpServer

class Worker(multiprocessing.Process):
    def __init__(self, connection, address):
        super().__init__()
        self.connection = connection
        self.address = address
        self.httpserver = HttpServer()

    def run(self):    
        full_request_bytes = b''
        try:
            self.connection.settimeout(3.0)
            while True:
                data = self.connection.recv(4096)
                if not data:
                    break
                full_request_bytes += data
        except socket.timeout:
            pass 
        except Exception as e:
            logging.error(f"Error saat menerima data dari {self.address}: {e}")
        finally:
            self.connection.settimeout(None)

        if full_request_bytes:
            try:
                hasil = self.httpserver.proses(full_request_bytes)
                self.connection.sendall(hasil)
            except Exception as e:
                logging.error(f"Error saat memproses/mengirim ke {self.address}: {e}")
        
        self.connection.close()
        logging.warning(f"Selesai, koneksi dengan {self.address} ditutup.")


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    my_socket.bind(('0.0.0.0', 8889))
    my_socket.listen(10) # Menaikkan antrian koneksi
    print("Server (Process Pool) berjalan di port 8889...")

    processes = []
    while True:
        try:
            connection, client_address = my_socket.accept()
            logging.warning("connection from {}".format(client_address))
            
            process = Worker(connection, client_address)
            process.start()
            
            connection.close()
            
            processes.append(process)
            processes = [p for p in processes if p.is_alive()]

        except KeyboardInterrupt:
            logging.warning("\nServer dihentikan oleh pengguna.")
            for p in processes:
                p.join(1) 
            break
        except Exception as e:
            logging.error(f"Error kritis di server utama: {e}")

if __name__ == "__main__":
    main()

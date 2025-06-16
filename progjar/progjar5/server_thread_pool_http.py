from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

def ProcessTheClient(connection, address):
    headers_data = b""
    while b"\r\n\r\n" not in headers_data:
        data = connection.recv(1024)
        if not data:
            break
        headers_data += data

    parts = headers_data.split(b'\r\n\r\n', 1)
    headers_part = parts[0]
    body_part = parts[1] if len(parts) > 1 else b""
    
    content_length = 0
    headers_str = headers_part.decode('utf-8', errors='ignore').split('\r\n')
    for header in headers_str:
        if header.lower().startswith('content-length:'):
            try:
                content_length = int(header.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
            break

    while len(body_part) < content_length:
        more_data = connection.recv(4096)
        if not more_data:
            break
        body_part += more_data
        
    full_request = headers_part + b'\r\n\r\n' + body_part

    if full_request:
        hasil = httpserver.proses(full_request)
        connection.sendall(hasil)

    connection.close()
    logging.warning(f"Selesai, koneksi dengan {self.address} ditutup.")
    return



def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 8885))
	my_socket.listen(1)

	with ThreadPoolExecutor(20) as executor:
		print("Server (Thread Pool) berjalan di port 8885...")
		while True:
				connection, client_address = my_socket.accept()
				logging.warning("connection from {}".format(client_address))
				
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)

				jumlah = ['x' for i in the_clients if i.running()==True]
				# print(f"Threads aktif: {len(jumlah)}")


def main():
	Server()

if __name__=="__main__":
	main()

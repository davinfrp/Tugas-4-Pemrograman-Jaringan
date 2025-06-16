import socket
import sys
import os
import re 

# 8885 untuk server thread pool, 8889 untuk server process pool.
SERVER_HOST = '172.16.16.101'
SERVER_PORT = 8889

def send_request(request):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            client_socket.sendall(request)
            
            response = b""
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data
            return response
    except ConnectionRefusedError:
        print(f"\n[ERROR] Koneksi ditolak. Pastikan server berjalan di {SERVER_HOST}:{SERVER_PORT}.\n")
        return None
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}\n")
        return None

def process_and_print_response(response_bytes):
    if not response_bytes:
        return

    try:
        header_bytes, body_bytes = response_bytes.split(b'\r\n\r\n', 1)
        header_str = header_bytes.decode('utf-8')
    except Exception:
        # Jika pemisahan gagal, cetak seluruh respons sebagai teks
        print(response_bytes.decode('utf-8', errors='ignore'))
        return

    print("\n--- Respons dari Server ---")
    print(header_str)
    print("-" * 27)

    content_type = ""
    for line in header_str.split('\r\n'):
        if line.lower().startswith('content-type:'):
            content_type = line.split(':', 1)[1].strip()
            break
    
    if 'text' in content_type:
        print(body_bytes.decode('utf-8', errors='ignore'))
    else:
        print(f"[Konten biner diterima, tipe: {content_type}, panjang: {len(body_bytes)} bytes]")
    print("---------------------------\n")

def list_files():
    print("Mengirim permintaan untuk melihat daftar file...")
    request = b"GET / HTTP/1.0\r\n\r\n"
    response_bytes = send_request(request)

    if not response_bytes:
        return
    try:
        response_str = response_bytes.decode('utf-8')
        header_part, body_part = response_str.split('\r\n\r\n', 1)

        if "HTTP/1.0 200 OK" in header_part and "Content-Type: text/html" in header_part:
            print("\n--- Daftar File di Server ---")
            
            sections = re.findall(r"<h2>(.*?)</h2><ul>(.*?)</ul>", body_part, re.DOTALL)
            
            if not sections:
                print("  Format daftar file tidak dikenali.")
            
            for title, list_html in sections:
                print(f"\n{title}")
                files = re.findall(r"<li><a.*?>(.*?)</a></li>", list_html)
                if files:
                    for f in files:
                        print(f"  - {f}")
                else:
                    if '<li>' in list_html:
                         print(f"  {list_html.strip('<li></ul>')}")
                    else:
                         print("  (Direktori kosong)")

            print("\n---------------------------\n")
        else:
            process_and_print_response(response_bytes)

    except Exception:
        process_and_print_response(response_bytes)

def upload_file():
    local_filepath = input("Masukkan path file lokal yang akan di-upload: ")
    
    if not os.path.exists(local_filepath) or not os.path.isfile(local_filepath):
        print(f"\n[ERROR] File '{local_filepath}' tidak ditemukan atau bukan file valid.\n")
        return

    with open(local_filepath, 'rb') as f:
        file_content = f.read()
    
    remote_filename = os.path.basename(local_filepath)
    print(f"Meng-upload '{local_filepath}' ke server sebagai '/uploads/{remote_filename}'...")

    request_line = f"POST /{remote_filename} HTTP/1.0\r\n"
    headers = f"Content-Length: {len(file_content)}\r\n"
    request = (request_line + headers + "\r\n").encode('utf-8') + file_content
    
    response_bytes = send_request(request)
    process_and_print_response(response_bytes)

def delete_file():
    remote_filepath = input("Masukkan path file di server yang akan dihapus (contoh: uploads/file.txt): ")
    if not remote_filepath:
        print("\n[ERROR] Nama file tidak boleh kosong.\n")
        return
        
    print(f"Mengirim permintaan untuk menghapus '{remote_filepath}'...")
    request = f"DELETE /{remote_filepath} HTTP/1.0\r\n\r\n".encode('utf-8')
    response_bytes = send_request(request)
    process_and_print_response(response_bytes)

def main():
    while True:
        print("--- Menu Klien HTTP ---")
        print("1. Lihat daftar file di server")
        print("2. Upload file ke server")
        print("3. Hapus file di server")
        print("4. Keluar")
        
        choice = input("Masukkan pilihan Anda (1-4): ")
        
        if choice == '1':
            list_files()
        elif choice == '2':
            upload_file()
        elif choice == '3':
            delete_file()
        elif choice == '4':
            print("Keluar dari program.")
            break
        else:
            print("\nPilihan tidak valid. Silakan masukkan angka dari 1 hingga 4.\n")

if __name__ == "__main__":
    main()

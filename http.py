import sys
import os
import os.path
import uuid
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.png'] = 'image/png'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'

        self.upload_dir = 'uploads'
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = [
            f"HTTP/1.0 {kode} {message}\r\n",
            f"Date: {tanggal}\r\n",
            "Connection: close\r\n",
            "Server: myserver/1.0\r\n",
            f"Content-Length: {len(messagebody)}\r\n"
        ]
        for kk, vv in headers.items():
            resp.append(f"{kk}: {vv}\r\n")
        resp.append("\r\n")

        response_headers = "".join(resp)

        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        return response_headers.encode() + messagebody

    def proses(self, data):
        try:
            headers_part, body_bytes = data.split(b'\r\n\r\n', 1)
        except ValueError:
            headers_part = data
            body_bytes = b''

        headers_str = headers_part.decode('utf-8', errors='ignore')
        requests = headers_str.split("\r\n")
        baris = requests[0]

        all_headers = [n for n in requests[1:] if n != '']
        headers_dict = {h.split(':', 1)[0].strip(): h.split(':', 1)[1].strip() for h in all_headers}

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, headers_dict)
            elif method == 'POST':
                # Body yang asli (bytes) diteruskan ke http_post
                return self.http_post(object_address, headers_dict, body_bytes)
            elif method == 'DELETE':
                return self.http_delete(object_address, headers_dict)
            else:
                return self.response(405, 'Method Not Allowed', 'Metode tidak didukung', {})
        except IndexError:
            return self.response(400, 'Bad Request', 'Request line tidak valid', {})

    def http_get(self, object_address, headers):
        if object_address == '/':
            try:
                root_files = [f for f in os.listdir('.') if os.path.isfile(f)]
                upload_files = os.listdir(self.upload_dir)
                
                html = "<h1>Daftar File di Server</h1>"
                html += "<h2>Direktori Utama:</h2><ul>"
                for f in root_files:
                    html += f'<li><a href="/{f}">{f}</a></li>'
                html += "</ul>"
                
                html += f"<h2>Direktori Uploads (/uploads):</h2><ul>"
                for f in upload_files:
                    html += f'<li><a href="/{self.upload_dir}/{f}">{f}</a></li>'
                html += "</ul>"
                
                return self.response(200, 'OK', html, {'Content-Type': 'text/html'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e), {})

        filepath = object_address.strip('/')
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return self.response(404, 'Not Found', f'File {filepath} tidak ditemukan', {})
        
        with open(filepath, 'rb') as fp:
            isi = fp.read()
        
        fext = os.path.splitext(filepath)[1].lower()
        content_type = self.types.get(fext, 'application/octet-stream')
        
        return self.response(200, 'OK', isi, {'Content-Type': content_type})

    def http_post(self, object_address, headers, body):
        filename = os.path.basename(object_address)
        if not filename:
            return self.response(400, 'Bad Request', 'Nama file tidak boleh kosong.', {})
            
        filepath = os.path.join(self.upload_dir, filename)

        try:
            with open(filepath, 'wb') as f:
                f.write(body)
            pesan = f'File {filename} berhasil di-upload ke direktori /{self.upload_dir}/'
            return self.response(201, 'Created', pesan, {})
        except Exception as e:
            return self.response(500, 'Internal Server Error', f'Gagal menyimpan file: {e}', {})

    def http_delete(self, object_address, headers):
        filepath = object_address.strip('/')
        
        if not os.path.exists(filepath):
             return self.response(404, 'Not Found', f'File {filepath} tidak ditemukan', {})
             
        if not os.path.isfile(filepath):
             return self.response(400, 'Bad Request', f'{filepath} bukanlah sebuah file', {})

        allowed_dir = os.path.abspath(self.upload_dir)
        file_dir = os.path.abspath(os.path.dirname(filepath))
        
        if not file_dir.startswith(allowed_dir) and file_dir != os.path.abspath('.'):
             return self.response(403, 'Forbidden', 'Tidak diizinkan menghapus file di luar direktori utama atau uploads.', {})
                 
        try:
            os.remove(filepath)
            return self.response(200, 'OK', f'File {filepath} berhasil dihapus.', {})
        except Exception as e:
            return self.response(500, 'Internal Server Error', f'Gagal menghapus file: {e}', {})

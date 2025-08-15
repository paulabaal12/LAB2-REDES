import socket
import json
import subprocess
import sys
import csv
import os

from utils.server_utils import write_files, create_files

algorithms = {
    "hamming": "./algorithms/HammingCode/decoder.py",
    "fletcher": "./algorithms/FletcherChecksum/decoder.py",
    "crc": "./algorithms/CRC-32/decoder.py"
}


def binary_to_ascii(bin_str):
    return ''.join(chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8))


TEST_MODE = len(sys.argv) > 1 and sys.argv[1] == '--test'

report_file = 'server_report.csv'
errors_file = 'errors.csv'

if TEST_MODE: create_files(report_file, errors_file)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5000))
server.listen(1)
print("Servidor escuchando en puerto 5000...")

while True:
    conn, addr = server.accept()
    data = conn.recv(4096).decode()
    payload = json.loads(data)
    algo = payload['algo']
    trama = payload['trama']
    num_msg = payload.get("NumMensaje", None)
    msg = None
    print(payload)

    print("==="*20)
    if algo not in algorithms:
        print("Algoritmo no soportado")
        conn.close()
        continue

    decoded = subprocess.check_output(["python", algorithms[algo], trama]).decode('utf-8', errors='replace').strip()

    fix_status = False
    if decoded.startswith("FIX"):
        fix_status = True
        decoded = decoded.split()[-1]  # último token como binario

    if decoded.startswith("ERROR"):
        print(decoded)
        if "Corregida:" in decoded:
            try:
                start_index = decoded.find("corregida:") + len("corregida:")                
                quote_start_index = decoded.find('"', start_index) + 1
                quote_end_index = decoded.find('"', quote_start_index)                
                binary_string = decoded[quote_start_index:quote_end_index]
                
                print(f"Trama corregida: {binary_string}")
                msg = binary_to_ascii(binary_string)
                print(f"Mensaje recibido: {msg}")
            
            except ValueError:
                # Maneja el caso en que las comillas no se encuentren
                print("No se pudo encontrar la cadena binaria corregida.")
    else:
        print(f"Trama recibida: {trama}")
        print(f"Decodificada: {decoded}")
        # Filtrar solo la línea binaria antes de convertir a ASCII
        if isinstance(decoded, str):
            lines = decoded.strip().splitlines()
            for line in lines:
                if set(line).issubset({'0', '1'}):
                    binary_line = line
                    break
            else:
                binary_line = lines[-1]  # fallback
        else:
            binary_line = decoded
        msg = binary_to_ascii(binary_line)
        print(f"Mensaje recibido: {msg}")
    
    if TEST_MODE and num_msg is not None:
        print(f"{num_msg}. {msg} con {algo}")
        write_files(msg, report_file, num_msg, algo, fix_status, errors_file)



    conn.close()

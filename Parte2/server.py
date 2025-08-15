import socket
import json
import subprocess
import sys
import csv
import os

algorithms = {
    "hamming": "./algorithms/HammingCode/decoder.py",
    "fletcher": "./algorithms/FletcherChecksum/decoder.py",
    "crc": "./algorithms/CRC-32/decoder.py"
}


def binary_to_ascii(bin_str):
    return ''.join(chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8))


TEST_MODE = len(sys.argv) > 1 and sys.argv[1] == '--test'

if TEST_MODE:
    report_file = 'server_report.csv'
    errors_file = 'errors.csv'
    if not os.path.exists(report_file):
        with open(report_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["NumMensaje","Algoritmo","MensajeRecibido","Fix","Success"])
    if not os.path.exists(errors_file):
        with open(errors_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["NumMensaje","Real","Falso"])

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
        # Leer el mensaje original desde client_report.csv
        with open('client_report.csv', newline='') as f:
            reader = csv.DictReader(f)
            if msg:
                orig_row = next((r for r in reader if int(r["NumMensaje"]) == msg), None)
            if orig_row:
                success = (orig_row["MensajeOriginalASCII"] == msg)
                with open(report_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([num_msg, algo, msg, fix_status, success])
                if not success:
                    with open(errors_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([num_msg, orig_row["MensajeOriginalASCII"], msg])
            else:
                with open(errors_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([None, None, None])


    conn.close()

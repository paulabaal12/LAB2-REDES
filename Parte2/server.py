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

def extract_binary_line(s: str):
    for line in s.splitlines():
        t = line.strip()
        if t and set(t) <= {"0", "1"}:
            return t
    return None

def safe_binary_to_ascii(bin_str: str):
    n = (len(bin_str) // 8) * 8
    if n == 0:
        return ""
    bin_str = bin_str[:n]
    return ''.join(chr(int(bin_str[i:i+8], 2)) for i in range(0, n, 8))

def run_generate_reports(run_id=None):
    base_dir = os.path.dirname(__file__)                 
    script  = os.path.join(base_dir, "reports", "generate_reports.py")
    in_dir  = base_dir                                   
    out_dir = os.path.join(base_dir, "reports", "out")   

    os.makedirs(out_dir, exist_ok=True)

    cmd = [sys.executable, script, "--in", in_dir, "--out", out_dir, "--stamp"]
    if run_id:  
        cmd += ["--run-id", str(run_id)]

    try:
        out = subprocess.check_output(cmd, encoding="utf-8", errors="replace", cwd=base_dir)
        print("=== Reporte de pruebas ===")
        print(out.strip())
        print("==========================")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar generate_reports.py: {e}")

# Estado para finish
max_processed_id = -1
pending_finish = False
finish_expected_last = None
finish_run_id = None

TEST_MODE = len(sys.argv) > 1 and sys.argv[1] == '--test'

report_file = 'server_report.csv'
errors_file = 'errors.csv'

if TEST_MODE:
    create_files(report_file, errors_file)

# ---------- Server socket ----------
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', 5000))
server.listen(1)
print("Servidor escuchando en puerto 5000...")

while True:
    conn, addr = server.accept()
    try:
        data = conn.recv(4096).decode()
        if not data:
            conn.close()
            continue

        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            print("Payload no es JSON válido desde el cliente.")
            conn.close()
            continue

        # --- Manejo de FINISH ---
        if payload.get("type") == "finish":
            expected = payload.get("expected_last")
            run_id   = payload.get("run_id")  # opcional
            if isinstance(expected, int) and max_processed_id >= expected:
                print(f" FINISH alcanzado (expected_last={expected}). Generando reportes…")
                run_generate_reports(run_id=run_id)
            else:
                pending_finish = True
                finish_expected_last = expected
                finish_run_id = run_id 
            conn.close()
            continue

        algo = payload.get('algo')
        trama = payload.get('trama', '')
        num_msg = payload.get("NumMensaje", None)
        msg = None

        print(payload)
        print("===" * 20)

        if algo not in algorithms:
            print("Algoritmo no soportado")
            conn.close()
            continue

        fix_status = False

        if algo == "hamming":
            try:
                decoded_raw = subprocess.check_output(
                    [sys.executable, algorithms[algo], "--json", trama],
                    encoding="utf-8",
                    errors="replace"
                ).strip()

                try:
                    d = json.loads(decoded_raw)  # salida estructurada del decoder
                except json.JSONDecodeError:
                    print("[hamming] Salida no-JSON; usando ruta de texto legacy")
                    decoded = subprocess.check_output(
                        [sys.executable, algorithms[algo], trama],
                        encoding="utf-8",
                        errors="replace"
                    ).strip()

                    if decoded.startswith("ERROR"):
                        print(decoded)
                        msg = ""
                    else:
                        print(f"Trama recibida: {trama}")
                        print(f"Decodificada: {decoded}")
                        binary_line = extract_binary_line(decoded) or decoded.splitlines()[-1]
                        msg = safe_binary_to_ascii(binary_line)
                        print(f"Mensaje recibido: {msg}")

                else:
                    status = d.get("status")
                    data_bits = d.get("data_bits", "")

                    print(f"Trama recibida: {trama}")
                    print(f"[hamming] Status: {status}")

                    if status == "FIX":
                        fix_status = True
                        fix = d.get("fix") or {}
                        print(f"Corrección Hamming: pos={fix.get('pos')}")
                        # print(f"Trama corregida: {fix.get('codeword')}")

                    msg = safe_binary_to_ascii(data_bits)
                    print(f"Mensaje recibido: {msg}")

            except subprocess.CalledProcessError as e:
                print(f"[hamming] Error al ejecutar decoder: {e}")
                msg = ""

        else:
            # Fletcher y CRC sin el json
            try:
                decoded = subprocess.check_output(
                    [sys.executable, algorithms[algo], trama],
                    encoding="utf-8",
                    errors="replace"
                ).strip()

                if decoded.startswith("ERROR"):
                    print(decoded)
                    msg = ""
                else:
                    print(f"Trama recibida: {trama}")
                    print(f"Decodificada: {decoded}")
                    binary_line = extract_binary_line(decoded) or decoded.splitlines()[-1]
                    msg = safe_binary_to_ascii(binary_line)
                    print(f"Mensaje recibido: {msg}")

            except subprocess.CalledProcessError as e:
                print(f"[{algo}] Error al ejecutar decoder: {e}")
                msg = ""

        if isinstance(num_msg, int):
            max_processed_id = max(max_processed_id, num_msg)

        if pending_finish and finish_expected_last is not None and max_processed_id >= finish_expected_last:
            print(f" Alcanzado expected_last={finish_expected_last}. Generando reportes…")
            run_generate_reports(run_id=finish_run_id)
            pending_finish = False
            finish_expected_last = None
            finish_run_id = None

        if TEST_MODE and num_msg is not None:
            print(f"{num_msg}. {msg} con {algo}")
            write_files(msg, report_file, num_msg, algo, fix_status, errors_file)

    except Exception as ex:
        print(f"Error inesperado en server: {ex}")

    conn.close()


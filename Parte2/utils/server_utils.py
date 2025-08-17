import json
import subprocess
import sys
import csv
import os

def create_files(report_file, errors_file):
    print("Escribiendo archivos de reporte...")
    if not os.path.exists(report_file):
        with open(report_file, 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["NumMensaje","Algoritmo","MensajeRecibido","Fix","Success"])
    else:
        # clean file
        with open(report_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["NumMensaje","Algoritmo", "MensajeRecibido","Fix","Success"])

    if not os.path.exists(errors_file):
        with open(errors_file, 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["NumMensaje","Real","Falso"])
    else:
        # clean file
        with open(errors_file, 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["NumMensaje","Real","Falso"])


def write_files(msg, report_file, num_msg, algo, fix_status, errors_file):
    # Leer el mensaje original desde client_report.csv
    with open('client_report.csv', newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if num_msg:
            orig_row = next((r for r in reader if int(r["NumMensaje"]) == num_msg), None)
            if orig_row:
                print(f"Mensaje original: {orig_row}")
                success = (orig_row["MensajeOriginalASCII"] == msg)
                if msg is None:
                    msg_string = "None"
                else:
                    msg_string = msg
                with open(report_file, 'a', newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([num_msg, algo, msg_string, fix_status, success])
                if not success and msg is not None:
                    with open(errors_file, 'a', newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([num_msg, orig_row["MensajeOriginalASCII"], msg])
        else:
            with open(errors_file, 'a', newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([None, None, None])
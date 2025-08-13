#!/usr/bin/env python3
# CRC32 - Receptor
# Uso:
#   python decoder.py in/msg1_crc32.txt in/msg2_crc32.txt --verbose

import sys, os

def is_binary(s: str) -> bool:
    return len(s) > 0 and all(c in "01" for c in s)

def binary_to_bytes(binary_str: str, byte_size: int = 8):
    """Convierte string binario a lista de enteros (bytes)"""
    bytes_list = []
    for i in range(0, len(binary_str), byte_size):
        block = binary_str[i:i + byte_size]
        if len(block) == byte_size:  # Solo procesar bloques completos
            bytes_list.append(int(block, 2))
    return bytes_list

def create_crc_table():
    poly = 0xedb88320
    table = []
    for i in range(256):
        c = i
        for j in range(8):
            if c & 1:
                c = poly ^ (c >> 1)
            else:
                c = c >> 1
        table.append(c & 0xffffffff)
    return table

crc_table = create_crc_table()

def crc32(data):
    crc = 0xffffffff
    for byte in data:
        crc = crc_table[(crc ^ byte) & 0xff] ^ (crc >> 8)
    return crc ^ 0xffffffff

def verify_crc(received_message: str, verbose: bool = False):
    """
    Verifica un mensaje con CRC32
    Retorna (status, original_data, info)
    status: "OK", "ERROR" 
    original_data: datos originales sin CRC
    info: información adicional para debug
    """
    
    checksum_bits = 32
    if len(received_message) < checksum_bits:
        return "ERROR", "", "Mensaje demasiado corto para contener CRC"
    
    data_part = received_message[:-checksum_bits]
    received_crc_str = received_message[-checksum_bits:]
    received_crc = int(received_crc_str, 2)
    if verbose:
        print(f"Mensaje recibido: {received_message}")
        print(f"Longitud total: {len(received_message)} bits")
        print(f"Parte de datos: {data_part} ({len(data_part)} bits)")
        print(f"CRC recibido: {received_crc_str} ({received_crc})")
    
    # Convertir datos a bytes
    if len(data_part) % 8 != 0:
        return "ERROR", "", "Los datos no son múltiplo de 8 bits"
    
    data_bytes = binary_to_bytes(data_part)
    
    if verbose:
        print(f"Bytes de datos: {data_bytes}")
        print(f"Bytes en hex: {[hex(b) for b in data_bytes]}")
    
    # Calcular CRC de los datos recibidos
    calculated_crc = crc32(data_bytes)
    if verbose:
        print(f"CRC calculado: {calculated_crc}")
    # Comparar CRCs
    if calculated_crc == received_crc:
        status = "OK"
        info = "CRCs coinciden"
    else:
        status = "ERROR"
        info = f"CRCs no coinciden: calculado {calculated_crc}; recibido {received_crc}"
    
    return status, data_part, info

def read_bits_file(path: str) -> str:
    """Lee un archivo y retorna su contenido binario"""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = "".join(line.strip().split())
            if s:
                return s
    return ""

def main():
    verbose = False
    files = []
    
    for arg in sys.argv[1:]:
        if arg == "--verbose":
            verbose = True
        else:
            files.append(arg)
    
    if len(files) < 1:
        print("Uso: python decoder.py <archivo1> [archivo2 ...] [--verbose]", file=sys.stderr)
        print("Los archivos pueden estar en cualquier carpeta (out/, in/, tests/, etc.)", file=sys.stderr)
        sys.exit(1)
    
    for file_path in files:
        if not os.path.isfile(file_path):
            print(f"No existe el archivo: {file_path}", file=sys.stderr)
            continue
        
        bits = read_bits_file(file_path)
        if not is_binary(bits):
            print(f"{file_path}: contenido no binario (solo 0/1 en una línea).", file=sys.stderr)
            continue
        
        if verbose:
            print(f"\n=== Procesando {file_path} ===")
        
        status, original_data, info = verify_crc(bits, verbose)
        
        filename = os.path.basename(file_path)
        
        if status == "OK":
            print(f"{filename} -> OK {original_data}")
        else:
            print(f"{filename} -> ERROR - Se detectaron errores")
            if verbose:
                print(f"  Detalles: {info}")
            print("  El mensaje se descarta por detectar errores.")

if __name__ == "__main__":
    main()
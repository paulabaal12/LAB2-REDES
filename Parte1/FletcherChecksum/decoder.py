#!/usr/bin/env python3
# Fletcher Checksum - Receptor
# Uso:
#   python decoder.py in/msg1_fletcher16.txt in/msg2_fletcher16.txt --verbose --block-size=16

import sys, os

def is_binary(s: str) -> bool:
    return len(s) > 0 and all(c in "01" for c in s)

def bytes_to_blocks(binary_str: str, block_size: int):
    """Convierte string binario a lista de enteros (bloques)"""
    blocks = []
    for i in range(0, len(binary_str), block_size):
        block = binary_str[i:i + block_size]
        if len(block) == block_size:  # Solo procesar bloques completos
            blocks.append(int(block, 2))
    return blocks

def fletcher_checksum(data, block_size: int):
    """Calcula Fletcher checksum"""
    modulus = (1 << block_size) - 1  # 2^block_size - 1
    sum1 = 0
    sum2 = 0
    
    for byte_val in data:
        sum1 = (sum1 + byte_val) % modulus
        sum2 = (sum2 + sum1) % modulus
    
    return (sum2 << block_size) | sum1

def verify_fletcher(received_message: str, block_size: int = 16, verbose: bool = False):
    """
    Verifica un mensaje con Fletcher checksum
    Retorna (status, original_data, info)
    status: "OK", "ERROR" 
    original_data: datos originales sin checksum
    info: información adicional para debug
    """
    
    if len(received_message) < block_size * 2:
        return "ERROR", "", "Mensaje demasiado corto para contener checksum"
    
    # Los últimos block_size*2 bits son el checksum
    checksum_bits = block_size * 2
    data_part = received_message[:-checksum_bits]
    received_checksum_str = received_message[-checksum_bits:]
    received_checksum = int(received_checksum_str, 2)
    
    if verbose:
        print(f"Mensaje recibido: {received_message}")
        print(f"Longitud total: {len(received_message)} bits")
        print(f"Parte de datos: {data_part} ({len(data_part)} bits)")
        print(f"Checksum recibido: {received_checksum_str} -> {received_checksum}")
    
    # Convertir datos a bloques
    if len(data_part) % block_size != 0:
        return "ERROR", "", f"Los datos no son múltiplo de {block_size} bits"
    
    data_blocks = bytes_to_blocks(data_part, block_size)
    
    if verbose:
        print(f"Bloques de datos: {data_blocks}")
        print(f"Bloques en hex: {[hex(b) for b in data_blocks]}")
    
    # Calcular checksum de los datos recibidos
    calculated_checksum = fletcher_checksum(data_blocks, block_size)
    
    if verbose:
        print(f"Checksum calculado: {calculated_checksum}")
        print(f"Checksum recibido:  {received_checksum}")
    
    # Comparar checksums
    if calculated_checksum == received_checksum:
        status = "OK"
        info = "Checksums coinciden"
    else:
        status = "ERROR"
        info = f"Checksums no coinciden: calculado={calculated_checksum}, recibido={received_checksum}"
    
    return status, data_part, info

def read_bits_file(path: str) -> str:
    """Lee un archivo y retorna su contenido binario"""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = "".join(line.strip().split())
            if s:
                return s
    return ""

def infer_block_size_from_filename(filename: str) -> int:
    """Intenta inferir el tamaño de bloque del nombre del archivo"""
    if 'fletcher8' in filename:
        return 8
    elif 'fletcher32' in filename:
        return 32
    else:
        return 16  # default

def main():
    verbose = False
    block_size = None
    files = []
    
    for arg in sys.argv[1:]:
        if arg == "--verbose":
            verbose = True
        elif arg.startswith("--block-size="):
            block_size = int(arg.split("=")[1])
        else:
            files.append(arg)
    
    # Validar tamaño de bloque
    if block_size and block_size not in [8, 16, 32]:
        print("Error: El tamaño de bloque debe ser 8, 16 o 32 bits", file=sys.stderr)
        sys.exit(1)
    
    if len(files) < 1:
        print("Uso: python fletcher_decoder.py <archivo1> [archivo2 ...] [--verbose] [--block-size=8|16|32]", file=sys.stderr)
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
        
        # Inferir tamaño de bloque si no se especificó
        current_block_size = block_size or infer_block_size_from_filename(file_path)
        
        if verbose:
            print(f"\n=== Procesando {file_path} ===")
            print(f"Tamaño de bloque: {current_block_size} bits")
        
        status, original_data, info = verify_fletcher(bits, current_block_size, verbose)
        
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
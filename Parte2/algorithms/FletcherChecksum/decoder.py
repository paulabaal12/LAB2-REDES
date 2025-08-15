#!/usr/bin/env python3
# Fletcher Checksum - Receptor
# Uso:
#   python decoder.py in/msg1_fletcher16.txt in/msg2_fletcher16.txt --verbose --block-size=16

import sys, os

def is_binary(s: str) -> bool:
    return len(s) > 0 and all(c in "01" for c in s)

def text_to_binary(text: str) -> str:
    return ''.join(f'{ord(c):08b}' for c in text)

def binary_to_text(binary_str: str) -> str:
    chars = []
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if len(byte) == 8:
            chars.append(chr(int(byte, 2)))
    return ''.join(chars)

def bytes_to_blocks(binary_str: str, block_size: int):
    """Convierte string binario a lista de enteros (bloques)"""
    blocks = []
    for i in range(0, len(binary_str), block_size):
        block = binary_str[i:i + block_size]
        if len(block) == block_size:
            blocks.append(int(block, 2))
    return blocks

def fletcher16_8(data):
    """Fletcher 16 sobre bloques de 8 bits"""
    sum1 = 0  
    sum2 = 0 
    modulus = 255  # para sumas parciales
    for b in data:
        sum1 = (sum1 + b) % modulus
        sum2 = (sum2 + sum1) % modulus
    # El checksum final es sum2 << 8 | sum1, pero en 16 bits
    return sum1, sum2, (sum2 << 8) | sum1

def fletcher_checksum(data, block_size: int):
    """Calcula Fletcher checksum"""
    modulus = (1 << block_size) - 1  # 2^block_size - 1
    sum1 = 0  
    sum2 = 0  
    for byte_val in data:
        sum1 = (sum1 + byte_val) % modulus
        sum2 = (sum2 + sum1) % modulus
    return sum1, sum2

def verify_fletcher(received_message: str, block_size: int = 16, verbose: bool = False):
    if len(received_message) < block_size * 2:
        return "ERROR", "", "Mensaje demasiado corto para contener checksum"
    
    # Los últimos block_size*2 bits son el checksum
    checksum_bits = block_size * 2
    data_part = received_message[:-checksum_bits]
    received_checksum_str = received_message[-checksum_bits:]
    # Ahora el orden es [sum2][sum1]
    received_sum2_str = received_checksum_str[:block_size]
    received_sum1_str = received_checksum_str[block_size:]
    received_sum2 = int(received_sum2_str, 2)
    received_sum1 = int(received_sum1_str, 2)
    if verbose:
        print(f"Mensaje recibido: {received_message}")
        print(f"Longitud total: {len(received_message)} bits")
        print(f"Parte de datos: {data_part} ({len(data_part)} bits)")
        print(f"Checksum recibido: sum1={received_sum1_str} ({received_sum1}), sum2={received_sum2_str} ({received_sum2})")
    
    # Convertir datos a bloques
    if len(data_part) % block_size != 0:
        return "ERROR", "", f"Los datos no son múltiplo de {block_size} bits"
    
    data_blocks = bytes_to_blocks(data_part, block_size)
    
    if verbose:
        print(f"Bloques de datos: {data_blocks}")
        print(f"Bloques en hex: {[hex(b) for b in data_blocks]}")
    
    # Calcular checksum de los datos recibidos
    calculated_sum1, calculated_sum2 = fletcher_checksum(data_blocks, block_size)
    if verbose:
        print(f"Checksum calculado: sum1={calculated_sum1}, sum2={calculated_sum2}")
    # Comparar checksums
    if calculated_sum1 == received_sum1 and calculated_sum2 == received_sum2:
        status = "OK"
        info = "Checksums coinciden"
    else:
        status = "ERROR"
        info = f"Checksums no coinciden: calculado sum1={calculated_sum1}, sum2={calculated_sum2}; recibido sum1={received_sum1}, sum2={received_sum2}"
    
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
        return 16 

def main():
    verbose = False
    block_size = 8 
    files = []
    
    for arg in sys.argv[1:]:
        if arg == "--verbose":
            verbose = True
        elif arg.startswith("--block-size="):
            block_size = int(arg.split("=")[1])
        elif arg == "--fletcher16_8":
            continue  
        else:
            files.append(arg)
    
    # Validar tamaño de bloque
    if block_size and block_size not in [4, 8, 16, 32]:
        print("Error: El tamaño de bloque debe ser 4, 8, 16 o 32 bits", file=sys.stderr)
        sys.exit(1)
    
    if len(files) < 1:
        print("Uso: python fletcher_decoder.py <archivo1> [archivo2 ...] [--verbose] [--block-size=8|16|32]", file=sys.stderr)
        print("Los archivos pueden estar en cualquier carpeta (out/, in/, tests/, etc.)", file=sys.stderr)
        sys.exit(1)
    
    for file_path in files:
        bits = None
        is_file = os.path.isfile(file_path)
        if is_file:
            bits = read_bits_file(file_path)
        else:
            # Tratar como cadena directa (texto o binario)
            bits = file_path.strip()

        # Si no es binario, convertir de texto ASCII a binario
        if not is_binary(bits):
            if verbose:
                print(f"{file_path}: El contenido no es binario, se asume texto ASCII y se convierte a binario.")
            bits = text_to_binary(bits)

        # Inferir tamaño de bloque si no se especificó
        current_block_size = block_size or (infer_block_size_from_filename(file_path) if is_file else 16)

        if verbose:
            print(f"\n=== Procesando {file_path if is_file else '[cadena directa]'} ===")
            print(f"Tamaño de bloque: {current_block_size} bits")

        # Modo especial: Fletcher-16 sobre bloques de 8 bits (estándar)
        if '--fletcher16_8' in sys.argv or (current_block_size == 8 and len(bits) == 48):
            filename = os.path.basename(file_path) if is_file else '[cadena directa]'
            data_blocks = bytes_to_blocks(bits[:-16], 8)
            sum1, sum2, checksum_calc = fletcher16_8(data_blocks)
            checksum_recv = int(bits[-16:], 2)
            if checksum_calc == checksum_recv:
                print("OK")
                print(bits[:-16])
            else:
                print("ERROR FLETCHER")
                print("Checksum invalido")
            if verbose:
                print(f"{filename} -> {'OK' if checksum_calc == checksum_recv else 'ERROR - Se detectaron errores'}")
                print(f"  Datos recibidos (sin checksum): {bits[:-16]}")
                print(f"  Detalle de verificación Fletcher 16 (bloques de 8 bits):")
                print(f"    Dato (bloque 8 bits)   Sum1   Sum2")
                sum1_step = 0  
                sum2_step = 0 
                for block in data_blocks:
                    sum1_step = (sum1_step + block) % 255
                    sum2_step = (sum2_step + sum1_step) % 255
                    print(f"    {format(block, '08b')} ({block})   {format(sum1_step, '08b')} ({sum1_step})   {format(sum2_step, '08b')} ({sum2_step})")
                calc_bits = format(checksum_calc, '016b')
                recv_bits = format(checksum_recv, '016b')
                if checksum_calc == checksum_recv:
                    print(f"  Checksum = {calc_bits} = {recv_bits}. OK")
                else:
                    print(f"  Checksum = {calc_bits} != {recv_bits}. ERROR")
        else:
            status, original_data, info = verify_fletcher(bits, current_block_size, verbose)
            # Salida simple para integración con servidor/cliente
            if status == "OK":
                print("OK")
                print(original_data)
            else:
                print("ERROR FLETCHER")
                print(info)

if __name__ == "__main__":
    main()
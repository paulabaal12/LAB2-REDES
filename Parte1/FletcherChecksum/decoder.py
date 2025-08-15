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
        if len(block) == block_size:
            blocks.append(int(block, 2))
    return blocks

def fletcher16_8(data):
    """Fletcher 16 sobre bloques de 8 bits"""
    sum1 = 1
    sum2 = 1
    modulus = 255  # para sumas parciales
    sum1_16 = 0
    sum2_16 = 0
    for b in data:
        sum1 = (sum1 + b) % modulus
        sum2 = (sum2 + sum1) % modulus
    # El checksum final es sum2 << 8 | sum1, pero en 16 bits
    return sum1, sum2, (sum2 << 8) | sum1
    return blocks

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
    received_sum1_str = received_checksum_str[:block_size]
    received_sum2_str = received_checksum_str[block_size:]
    received_sum1 = int(received_sum1_str, 2)
    received_sum2 = int(received_sum2_str, 2)
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
        
        # Modo especial: Fletcher 16 sobre bloques de 8 bits
        if '--fletcher16_8' in sys.argv:
            filename = os.path.basename(file_path)
            data_blocks = bytes_to_blocks(bits[:-16], 8)
            sum1, sum2, checksum_calc = fletcher16_8(data_blocks)
            checksum_recv = int(bits[-16:], 2)
            print(f"{filename} -> {'OK' if checksum_calc == checksum_recv else 'ERROR - Se detectaron errores'}")
            print(f"  Datos recibidos (sin checksum): {bits[:-16]}")
            print(f"  Detalle de verificación Fletcher 16 (bloques de 8 bits):")
            print(f"    Dato (bloque 8 bits)   Sum1   Sum2")
            sum1_step = 1
            sum2_step = 1
            for block in data_blocks:
                sum1_step = (sum1_step + block) % 255
                sum2_step = (sum2_step + sum1_step) % 255
                print(f"    {format(block, '08b')} ({block})   {format(sum1_step, '08b')} ({sum1_step})   {format(sum2_step, '08b')} ({sum2_step})")
            calc_bits = format(checksum_calc, '016b')
            recv_bits = format(checksum_recv, '016b')
            print(f"  Checksum = {calc_bits} ≠ {recv_bits}. ERROR")
    else:
        status, original_data, info = verify_fletcher(bits, current_block_size, verbose)
        filename = os.path.basename(file_path)
        if status == "OK":
            # Mostrar checksum calculado y recibido solo si los datos son válidos
            if original_data and len(original_data) % current_block_size == 0:
                data_blocks = bytes_to_blocks(original_data, current_block_size)
                calc_sum1, calc_sum2 = fletcher_checksum(data_blocks, current_block_size)
                sum1_bits = format(calc_sum1, f'0{current_block_size}b')
                sum2_bits = format(calc_sum2, f'0{current_block_size}b')
                received_checksum_str = bits[-current_block_size*2:]
                received_sum1_str = received_checksum_str[:current_block_size]
                received_sum2_str = received_checksum_str[current_block_size:]
                calc_full = f"{sum2_bits}{sum1_bits}"
                recv_full = f"{received_sum2_str}{received_sum1_str}"
                print(f"{filename} -> OK {original_data}")
                print(f"  Checksum = {calc_full} = {recv_full}")
            else:
                print(f"{filename} -> OK {original_data}")
        else:
            print(f"{filename} -> ERROR - Se detectaron errores")
            print("  El mensaje se descarta por detectar errores.")
            if original_data:
                print(f"  Datos recibidos (sin checksum): {original_data}")
                data_blocks = bytes_to_blocks(original_data, current_block_size)
                if data_blocks:
                    print(f"    Dato (bloque {current_block_size} bits)   Sum1   Sum2")
                    modulus = (1 << current_block_size) - 1
                    sum1 = 1
                    sum2 = 1
                    for i, block in enumerate(data_blocks):
                        sum1 = (sum1 + block) % modulus
                        sum2 = (sum2 + sum1) % modulus
                        # Formato alineado
                        block_bin = format(block, f'0{current_block_size}b')
                        sum1_bin = format(sum1, f'0{current_block_size}b')
                        sum2_bin = format(sum2, f'0{current_block_size}b')
                        print(f"    {block_bin:<{current_block_size}} ({block:>3})   {sum1_bin:<{current_block_size}} ({sum1:>3})   {sum2_bin:<{current_block_size}} ({sum2:>3})")
                    calc_sum1, calc_sum2 = fletcher_checksum(data_blocks, current_block_size)
                    sum1_bits = format(calc_sum1, f'0{current_block_size}b')
                    sum2_bits = format(calc_sum2, f'0{current_block_size}b')
                    received_checksum_str = bits[-current_block_size*2:]
                    received_sum1_str = received_checksum_str[:current_block_size]
                    received_sum2_str = received_checksum_str[current_block_size:]
                    # Mostrar checksums en una sola línea, resaltando diferencias
                    calc_full = f"{sum2_bits}{sum1_bits}"
                    recv_full = f"{received_sum2_str}{received_sum1_str}"
                    print(f"  Checksum = {calc_full} ≠ {recv_full}. ERROR")
                else:
                    print(f"  Nota: La parte de datos extraída no es múltiplo de {current_block_size} bits, por lo que no se puede calcular el checksum esperado.")
            else:
                print("  Forma correcta esperada (sin checksum): <vacío>")
                print("  Nota: No se pudo extraer la parte de datos original, probablemente por longitud inválida o formato incorrecto.")

if __name__ == "__main__":
    main()
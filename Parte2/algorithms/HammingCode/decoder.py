#!/usr/bin/env python3
# Código Hamming - Receptor
# Uso:
#   python decoder.py in/msg1_ok.txt in/msg2_err1.txt --verbose

import sys, os

def is_binary(s: str) -> bool:
    return len(s) > 0 and all(c in "01" for c in s)

def is_pow2(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def infer_r_from_n(n: int) -> int:
    r = 0
    while (1 << r) < (n + 1):
        r += 1
    return r

def decode_hamming(codeword: str, verbose: bool=False):
    """
    Devuelve (status, message_bits, fixed_pos)
    status: "OK" o "FIX"
    message_bits: str (datos sin paridades)
    fixed_pos: int | None
    """
    n = len(codeword)
    r = infer_r_from_n(n)

    # La posición del array empieza en 1
    code = [0] * (n + 1) 
    for i, ch in enumerate(codeword, start=1):
        code[i] = int(ch)

    syndrome = 0 # código de error
    if verbose:
        print(f"n={n}, r={r}")
        print("Trama recibida:", codeword)

    for i in range(r):
        p = 1 << i
        parity = 0
        for pos in range(1, n + 1):
            if pos & p:
                parity ^= code[pos]
        if parity != 0:
            syndrome |= p

    if verbose:
        print(f"Síndrome (dec)={syndrome}, (bin)={syndrome:0{r}b}")

    fixed_pos = None
    fixed_code = None

    if syndrome == 0:
        status = "OK"
    elif 1 <= syndrome <= n:
        code[syndrome] ^= 1  
        fixed_pos = syndrome
        fixed_code = "".join(str(bit) for bit in code[1:])
        if verbose:
            print(f"Se corrige bit en posición {syndrome}.")
            print(f"Trama corregida: {fixed_code}")
        status = "FIX"
    else:
        status = "DROP"

    # Extraer solo datos (posiciones que NO son potencias de 2)
    data_bits = []
    for pos in range(1, n + 1):
        if not is_pow2(pos):
            data_bits.append(str(code[pos]))
    message = "".join(data_bits)

    return status, message, fixed_pos, fixed_code

def read_bits_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = "".join(line.strip().split())
            if s:
                return s
    return ""

def main():
    verbose = False
    files = []
    for a in sys.argv[1:]:
        if a == "--verbose":
            verbose = True
        else:
            files.append(a)

    if len(files) < 1:
        print("Uso: python decoder.py <archivo1> [archivo2 ...] [--verbose]", file=sys.stderr)
        sys.exit(1)

    for p in files:
        if not os.path.isfile(p):
            print(f"No existe el archivo: {p}", file=sys.stderr)
            continue

        bits = read_bits_file(p)
        if not is_binary(bits):
            print(f"{p}: contenido no binario (solo 0/1 en una línea).", file=sys.stderr)
            continue

        status, msg, pos, fixed_code = decode_hamming(bits, verbose=verbose)

        if status == "OK":
            print(f"{os.path.basename(p)} -> OK {msg}")
        elif status == "FIX":
            if not verbose and fixed_code is not None:
                print(f"Trama corregida: {fixed_code}")
            print(f"{os.path.basename(p)} -> FIX pos={pos} {msg}")
        else:  # DROP
            print(f"{os.path.basename(p)} -> DROP (errores no corregibles)")

if __name__ == "__main__":
    main()

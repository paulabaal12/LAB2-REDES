#!/usr/bin/env node
// Código de Hamming - Transmisor
// Uso:
//   # Múltiples archivos -> guarda en out/<base>_trama.txt
//   node encoder.js tests/msg1.txt tests/msg2.txt --verbose (para ver el procedimiento)
//
//   # Un archivo
//   node encoder.js tests/msg1.txt
//   node encoder.js tests/msg1.txt --verbose (para ver el procedimiento)
//
//   node encoder.js 1011001
//   node encoder.js 1011001 --verbose
//

const fs = require('fs');
const path = require('path');

function isBinary(str) {
    return /^[01]+$/.test(str);
}
function isPow2(x) {
    return (x & (x - 1)) === 0;
}
function minimumR(m) {
    let r = 0;
    while (m + r + 1 > (1 << r)) r++;
    return r;
}

function fail(msg) {
    console.error('Error:', msg);
    process.exit(1);
}

function encodeHamming(dataBits, { verbose = false } = {}) {
    const m = dataBits.length;
    const r = minimumR(m);
    const n = m + r;

    const code = new Array(n + 1).fill(0); // Empezamos el array con la posición 1

    // Colocar datos en posiciones NO potencias de 2
    let idx = 0;
    for (let pos = 1; pos <= n; pos++) {
        if (!isPow2(pos)) {
            code[pos] = Number(dataBits[idx++]);
        }
    }

    if (verbose) {
        console.log(`m=${m}, r=${r}, n=${n}  (condición: m+r+1 ≤ 2^r)`);
        console.log('Posiciones: ', [...Array(n).keys()].map(i => i + 1).join(' '));
        console.log('Mapa inicial (P=paridad, número=dato):');
        let line = '';
        for (let pos = 1; pos <= n; pos++) {
            line += isPow2(pos) ? 'P' : code[pos];
            line += (pos < n ? ' ' : '');
        }
        console.log(' ', line);
    }

    // Calcular bits de paridad
    for (let i = 0; i < r; i++) {
        const p = 1 << i; // posición del bit de paridad
        let parity = 0;
        const covered = [];
        for (let pos = 1; pos <= n; pos++) {
            if (pos & p) {
                parity ^= code[pos];
                covered.push(pos);
            }
        }
        code[p] = parity; // paridad calculada
        if (verbose) {
            console.log(`P${p} cubre posiciones: ${covered.join(', ')} → XOR = ${parity}`);
        }
    }

    const codeword = code.slice(1).join('');
    if (verbose) {
        console.log('Trama codificada final:', codeword);
    }
    return codeword;
}

// ===== main =====
const rawArgs = process.argv.slice(2);
const verbose = rawArgs.includes('--verbose');
const args = rawArgs.filter(a => a !== '--verbose');

if (args.length >= 1) {
    let processed = 0;

    args.forEach((token) => {
        let bits = null;

        if (isBinary(token)) {
            bits = token;
        } else {
            const abs = path.resolve(token);
            if (fs.existsSync(abs) && fs.statSync(abs).isFile()) {
                const content = fs.readFileSync(abs, 'utf8').trim();
                if (!isBinary(content)) {
                    console.error(`${token}: el contenido no es binario (solo 0/1 en una línea).`);
                    return;
                }
                bits = content;
            } else {
                console.error(`No existe el archivo o no es binario válido: ${token}`);
                return;
            }
        }

        const trama = encodeHamming(bits, { verbose });
        console.log(trama);

        processed++;
    });

    if (processed === 0) {
        fail('Ningún argumento válido. Usa binarios directos (0/1) o archivos existentes.');
    }
    process.exit(0);
}

fail('Uso: node encoder.js <bits|archivo1> [archivo2 ...] [--verbose]');

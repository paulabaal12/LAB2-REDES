#!/usr/bin/env node
// Código de Hamming
// Uso:
//   # Múltiples archivos -> guarda en out/<base>_trama.txt
//   node encoder.js tests/msg1.txt tests/msg2.txt --verbose (para ver el procedimiento)
//
//   # Un archivo
//   node encoder.js tests/msg1.txt
//   node encoder.js tests/msg1.txt --verbose (para ver el procedimiento)
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
    const outDir = path.resolve(__dirname, 'out');
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

    args.forEach((filePath) => {
        const abs = path.resolve(filePath);
        if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
            console.error(`No existe el archivo: ${filePath}`);
            return;
        }
        const bits = fs.readFileSync(abs, 'utf8').trim();
        if (!isBinary(bits)) {
            console.error(`${filePath}: el contenido no es binario (solo 0/1 en una línea).`);
            return;
        }
        const base = path.basename(filePath, path.extname(filePath));
        const label = `${base} (${bits})`;
        const trama = encodeHamming(bits, { verbose, label });

        const outFile = path.join(outDir, `${base}_trama.txt`);
        fs.writeFileSync(outFile, trama + '\n');
        console.log(`✔ ${filePath} → ${outFile}`);
    });
    process.exit(0);
}

// Si se llega aquí, no hubo archivos ni bits válidos
fail('Uso: node encoder.js <archivo1> [archivo2 ...] [--verbose] ');

#!/usr/bin/env node
// CRC32 - Transmisor
// Uso:
//   node encoder.js tests/msg1.txt tests/msg2.txt --verbose

const fs = require('fs');
const path = require('path');

function isBinary(str) {
    return /^[01]+$/.test(str);
}

function fail(msg) {
    console.error('Error:', msg);
    process.exit(1);
}

const table = (function () {
    const poly = 0xEDB88320;
    let values = new Uint32Array(256);
    for (let i = 0; i < 256; i++) {
        let c = i;
        for (let j = 0; j < 8; j++) {
            if (c & 1) {
                c = poly ^ (c >>> 1);
            } else {
                c = c >>> 1;
            }
        }
        values[i] = c;
    }
    return values;
})();

function crc32(byte_array, checksum = 0) {
    checksum ^= 0xFFFFFFFF;
    for (let byte of byte_array) {
        checksum = (checksum >>> 8) ^ table[(checksum ^ byte) & 0xFF];
    }
    return (checksum ^ 0xFFFFFFFF) >>> 0;
}

function binaryToBytes(binaryStr) {
    const bitsPerByte = 8;
    let padding = (bitsPerByte - binaryStr.length % bitsPerByte) % bitsPerByte;
    let padded = binaryStr;
    if (padding !== 0) {
        padded += '0'.repeat(padding);
        console.log(`Se agregó padding de ${padding} bits para completar bytes de ${bitsPerByte} bits`);
    }
    
    const bytes = [];
    for (let i = 0; i < padded.length; i += bitsPerByte) {
        const block = padded.substr(i, bitsPerByte);
        bytes.push(parseInt(block, 2));
    }
    
    return {bytes, padded};
}

function encodeWithCrc(dataBits, verbose = false) {
    if (verbose) {
        console.log(`Mensaje original: ${dataBits} (${dataBits.length} bits)`);
    }
    
    // Convertir bits a bytes
    const {bytes: dataBytes, padded: paddedData} = binaryToBytes(dataBits);
    
    // Calcular CRC
    const crcValue = crc32(dataBytes);
    
    const crcBits = crcValue.toString(2).padStart(32, '0');
    
    // Mensaje completo = datos con padding + CRC
    const fullMessage = paddedData + crcBits;
    
    if (verbose) {
        console.log(`Datos con padding: ${paddedData}`);
        console.log(`CRC en binario: ${crcBits}`);
        console.log(`Mensaje completo: ${fullMessage}`);
    }
    
    return {
        originalBits: dataBits,
        paddedData: paddedData,
        crcBits: crcBits,
        fullMessage: fullMessage
    };
}

// ===== main =====
const rawArgs = process.argv.slice(2);
const verbose = rawArgs.includes('--verbose');

const args = rawArgs.filter(a => !a.startsWith('--'));

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
        
        console.log(`\n=== Procesando ${filePath} ===`);
        const result = encodeWithCrc(bits, verbose);
        
        const base = path.basename(filePath, path.extname(filePath));
        const outFile = path.join(outDir, `${base}_crc32.txt`);
        fs.writeFileSync(outFile, result.fullMessage + '\n');
        
        console.log(`✔ ${filePath} → ${outFile}`);
        console.log(`  Mensaje original: ${bits.length} bits`);
        console.log(`  Mensaje con CRC32: ${result.fullMessage.length} bits`);
        console.log(`  Overhead: ${result.fullMessage.length - bits.length} bits (32 bits de CRC + padding)`);
    });
    
    process.exit(0);
}

// Si se llega aquí, no hubo archivos válidos
fail('Uso: node encoder.js <archivo1> [archivo2 ...] [--verbose]');
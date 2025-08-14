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
const verbose = process.argv.includes('--verbose');

const args = process.argv.filter(a => !a.startsWith('--'));
if (args.length >= 3) {
    const bits = args[2].trim();

    if (!isBinary(bits)) {
        console.error(`El contenido no es binario (solo 0/1 en una línea).`);
        process.exit(1);
    }

    const result = encodeWithCrc(bits, verbose);

    // Debug solo si verbose
    if (verbose) {
        console.error(`Mensaje original: ${bits.length} bits`);
        console.error(`Mensaje con CRC32: ${result.fullMessage.length} bits`);
        console.error(`Overhead: ${result.fullMessage.length - bits.length} bits (32 bits de CRC + padding)`);
        console.error(`CRC-32: ${result.crcBits}`);
        console.error(`Mensaje final enviado:`);
    }

    // Salida pura para el cliente/servidor: solo el binario
    console.log(result.fullMessage);

    process.exit(0);
}

console.error('Uso: node CRC_encoder.js "<cadena_binaria>" [--verbose]');
process.exit(1);



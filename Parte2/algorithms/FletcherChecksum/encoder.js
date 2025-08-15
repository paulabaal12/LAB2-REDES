#!/usr/bin/env node
// Fletcher Checksum - Transmisor
// Uso:
//   node encoder.js tests/msg1.txt tests/msg2.txt --verbose --block-size=16
//   node encoder.js tests/msg1.txt --block-size=8

const fs = require('fs');
const path = require('path');

function isBinary(str) {
    return /^[01]+$/.test(str);
}

function fail(msg) {
    console.error('Error:', msg);
    process.exit(1);
}

function binaryToBytes(binaryStr, blockSize) {
    // Agregar padding si es necesario
    const bitsPerBlock = blockSize;
    const remainder = binaryStr.length % bitsPerBlock;
    let padding = 0;
    if (remainder !== 0) {
        padding = bitsPerBlock - remainder;
        binaryStr += '0'.repeat(padding);
    }
    const blocks = [];
    for (let i = 0; i < binaryStr.length; i += bitsPerBlock) {
        const block = binaryStr.substr(i, bitsPerBlock);
        blocks.push(parseInt(block, 2));
    }
    return { blocks, padding };
}

function fletcherChecksum(data, blockSize, verbose = false) {
    const modulus = blockSize === 32 ? Math.pow(2, 32) - 1 : (1 << blockSize) - 1; // 2^blockSize - 1
    let sum1 = 0;
    let sum2 = 0;
    
    if (verbose) {
        console.log(`Calculando Fletcher checksum con bloques de ${blockSize} bits`);
        console.log(`Módulo: ${modulus} (0x${modulus.toString(16)})`);
        console.log('Datos por bloques:', data.map(d => `${d} (0x${d.toString(16)})`).join(', '));
    }
    
    for (let i = 0; i < data.length; i++) {
        sum1 = (sum1 + data[i]) % modulus;
        sum2 = (sum2 + sum1) % modulus;
        
        if (verbose) {
            console.log(`Bloque ${i+1}: dato=${data[i]}, sum1=${sum1}, sum2=${sum2}`);
        }
    }
    
    const checksum = (sum2 << blockSize) | sum1;
    
    if (verbose) {
        console.log(`Checksum final: sum1=${sum1}, sum2=${sum2}`);
        console.log(`Checksum combinado: ${checksum} (0x${checksum.toString(16)})`);
    }
    
    return checksum;
}

function encodeWithFletcher(dataBits, blockSize = 16, verbose = false) {
    if (verbose) {
        console.log(`Mensaje original: ${dataBits} (${dataBits.length} bits)`);
    }
    
    // Convertir bits a bloques
    const { blocks: dataBlocks, padding } = binaryToBytes(dataBits, blockSize);

    if (verbose) {
        console.log(`\n--- Procedimiento detallado Fletcher${blockSize} ---`);
        if (padding > 0) {
            console.log(`Se agregó padding de ${padding} bits para completar bloques de ${blockSize} bits.`);
        } else {
            console.log('No se agregó padding.');
        }
        console.log('Bloques:');
        dataBlocks.forEach((b, i) => {
            const bin = b.toString(2).padStart(blockSize, '0');
            console.log(`  Bloque ${i+1}: ${bin} (decimal: ${b})`);
        });
    }

    // Calcular checksum paso a paso
    const modulus = blockSize === 32 ? Math.pow(2, 32) - 1 : (1 << blockSize) - 1;
    let sum1 = 0;
    let sum2 = 0;
    if (verbose) {
        console.log(`\nCálculo de sumas parciales (modulo ${modulus}):`);
    }
    for (let i = 0; i < dataBlocks.length; i++) {
        sum1 = (sum1 + dataBlocks[i]) % modulus;
        sum2 = (sum2 + sum1) % modulus;
        if (verbose) {
            const bin1 = sum1.toString(2).padStart(blockSize, '0');
            const bin2 = sum2.toString(2).padStart(blockSize, '0');
            console.log(`  Iteración ${i+1}: sum1=${sum1} (${bin1}), sum2=${sum2} (${bin2})`);
        }
    }

    // Mostrar cómo se arma el checksum
    const sum1Bits = sum1.toString(2).padStart(blockSize, '0');
    const sum2Bits = sum2.toString(2).padStart(blockSize, '0');
    const checksumBits = sum1Bits + sum2Bits;
    if (verbose) {
        console.log(`\nChecksum:`);
        console.log(`  sum1: ${sum1} (${sum1Bits})`);
        console.log(`  sum2: ${sum2} (${sum2Bits})`);
        console.log(`  Checksum combinado: ${checksumBits}`);
    }

    // Mensaje completo = datos originales (con padding si se aplicó) + checksum
    const paddedData = dataBlocks.map(block => 
        block.toString(2).padStart(blockSize, '0')
    ).join('');
    const fullMessage = paddedData + checksumBits;

    if (verbose) {
        console.log(`\nMensaje final:`);
        console.log(`  Datos (con padding): ${paddedData}`);
        console.log(`  Checksum:           ${checksumBits}`);
        console.log(`  Mensaje completo:   ${fullMessage}`);
        console.log('  [datos][checksum]');
    }

    return {
        originalBits: dataBits,
        paddedData: paddedData,
        checksumBits: checksumBits,
        fullMessage: fullMessage,
        blockSize: blockSize
    };
}

// ===== main =====
const rawArgs = process.argv.slice(2);
const verbose = rawArgs.includes('--verbose');
const blockSizeArg = rawArgs.find(arg => arg.startsWith('--block-size='));
const blockSize = blockSizeArg ? parseInt(blockSizeArg.split('=')[1]) : 16;

// Validar tamaño de bloque
if (![4, 8, 16, 32].includes(blockSize)) {
    fail('El tamaño de bloque debe ser 4, 8, 16 o 32 bits');
}

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

        if (verbose) {
            console.log(`\n=== Procesando ${filePath} ===`);
        }
        const result = encodeWithFletcher(bits, blockSize, verbose);

        const base = path.basename(filePath, path.extname(filePath));
        const outFile = path.join(outDir, `${base}_fletcher${blockSize}.txt`);
        fs.writeFileSync(outFile, result.fullMessage + '\n');

        if (verbose) {
            console.log(`✔ Archivo generado: ${outFile}`);
            console.log(`  Mensaje original: ${bits.length} bits`);
            console.log(`  Mensaje con Fletcher: ${result.fullMessage.length} bits`);
            console.log(`  Overhead: ${result.fullMessage.length - bits.length} bits (${blockSize*2} bits de checksum + padding)`);
        } else {
            console.log(`✔ Archivo generado: ${outFile}`);
        }
    });

    process.exit(0);
}

// Si se llega aquí, no hubo archivos válidos
fail('Uso: node fletcher_encoder.js <archivo1> [archivo2 ...] [--verbose] [--block-size=8|16|32]');
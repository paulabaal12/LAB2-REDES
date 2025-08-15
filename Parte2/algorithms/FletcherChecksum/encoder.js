// Fletcher Checksum - Transmisor
// Uso:
//   node encoder.js tests/msg1.txt tests/msg2.txt --verbose --block-size=16
//   node encoder.js tests/msg1.txt --block-size=8

// Convierte un string binario a bloques de tamaño blockSize
function binaryToBytes(binaryStr, blockSize) {
    const blocks = [];
    for (let i = 0; i < binaryStr.length; i += blockSize) {
        let chunk = binaryStr.slice(i, i + blockSize);
        if (chunk.length === blockSize) {
            blocks.push(parseInt(chunk, 2));
        }
        // Si el último bloque es incompleto, lo ignoramos (no padding)
    }
    return { blocks, padding: 0 };
}

// Implementación principal del encoder Fletcher
function encodeWithFletcher(dataBits, blockSize = 8, verbose = false) {
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
    const checksumBits = sum2Bits + sum1Bits; // [sum2][sum1]
    if (verbose) {
        console.log(`\nChecksum:`);
        console.log(`  sum1: ${sum1} (${sum1Bits})`);
        console.log(`  sum2: ${sum2} (${sum2Bits})`);
        console.log(`  Checksum combinado: ${checksumBits}`);
    }
    // Mensaje completo = datos originales (con padding si se aplicó) + checksum
    const dataBin = dataBlocks.map(block => block.toString(2).padStart(blockSize, '0')).join('');
    const fullMessage = dataBin + checksumBits;
    if (verbose) {
        console.log(`\nMensaje final:`);
        console.log(`  Datos: ${dataBin}`);
        console.log(`  Checksum:           ${checksumBits}`);
        console.log(`  Mensaje completo:   ${fullMessage}`);
        console.log('  [datos][checksum]');
    }
    return {
        originalBits: dataBits,
        dataBin: dataBin,
        checksumBits: checksumBits,
        fullMessage: fullMessage,
        blockSize: blockSize
    };
}

const fs = require('fs');
const path = require('path');

// ===== main =====
function fail(msg) {
    console.error('Error:', msg);
    process.exit(1);
}

function isBinary(str) {
    return /^[01]+$/.test(str);
}

function textToBinary(text) {
    return text.split('').map(c => c.charCodeAt(0).toString(2).padStart(8, '0')).join('');
}

// ===== main =====
const rawArgs = process.argv.slice(2);
const verbose = rawArgs.includes('--verbose');

// Forzar siempre bloques de 8 bits para Fletcher
const blockSize = 8;

// Validar tamaño de bloque
if (![4, 8, 16, 32].includes(blockSize)) {
    fail('El tamaño de bloque debe ser 4, 8, 16 o 32 bits');
}

// Directorio de salida
const outDir = 'out'; 
if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir);
}

// Filtrar argumentos que no son flags para procesar como archivos o cadenas
const args = rawArgs.filter(arg => !arg.startsWith('--'));

if (args.length >= 1) {
    args.forEach((inputArg) => {
        let content;
        let isFile = false;
        const abs = path.resolve(inputArg);
        if (fs.existsSync(abs) && fs.statSync(abs).isFile()) {
            content = fs.readFileSync(abs, 'utf8').trim();
            isFile = true;
        } else {
            // No es archivo, tratar como cadena directa (texto o binario)
            content = inputArg.trim();
        }

        let bits;
        if (isBinary(content)) {
            bits = content;
        } else {
            // Convertir texto ASCII a binario
            bits = textToBinary(content);
            if (verbose) {
                console.log(`Entrada de texto ASCII. Convertido a binario: ${bits}`);
            }
        }

        if (verbose) {
            console.log(`\n=== Procesando ${isFile ? inputArg : '[cadena directa]'} ===`);
        }
        const result = encodeWithFletcher(bits, blockSize, verbose);

        if (isFile) {
            const base = path.basename(inputArg, path.extname(inputArg));
            const outFile = path.join(outDir, `${base}_fletcher${blockSize}.txt`);
            fs.writeFileSync(outFile, result.fullMessage + '\n');
            if (verbose) {
                console.log(`✓ Archivo generado: ${outFile}`);
                console.log(`  Mensaje original: ${bits.length} bits`);
                console.log(`  Mensaje con Fletcher: ${result.fullMessage.length} bits`);
                console.log(`  Overhead: ${result.fullMessage.length - bits.length} bits (${blockSize*2} bits de checksum + padding)`);
            } else {
                console.log(`✓ Archivo generado: ${outFile}`);
            }
        } else {
            // Salida pura para uso en consola
            console.log(result.fullMessage);
        }
    });

    process.exit(0);
} else {
    // Si se llega aquí, no hubo archivos válidos
    fail('Uso: node fletcher_encoder.js <archivo1> [archivo2 ...] [--verbose] [--block-size=8|16|32]');
}
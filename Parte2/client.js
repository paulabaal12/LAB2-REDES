const net = require('net');
const readline = require('readline');
const { execFileSync } = require('child_process');
const fs = require('fs');

const { asciiToBinary, applyNoise , randomAsciiString} = require('./utils/client_utils.js');


const algorithms = {
        //"hamming": "./algorithms/HammingCode/encoder.js",
        "crc": "./algorithms/CRC-32/encoder.js",
        "fletcher": "./algorithms/FletcherChecksum/encoder.js",
};



const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

// Función para envolver rl.question en una Promesa
function askQuestion(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

function processInput(p, asciiMsg, algo){
    const binMsg = asciiToBinary(asciiMsg);
    const encoded = execFileSync('node', [algorithms[algo], binMsg]).toString().trim();
    const noisy = applyNoise(encoded, p);
    const bitsFlipped = noisy.split('').reduce((acc, bit, idx) => acc + (bit !== encoded[idx] ? 1 : 0), 0);

    return {binMsg, encoded, noisy, bitsFlipped};
}

// Función principal que ejecutará el bucle de envío
async function startSending() {
    while (true) {

        const msg = await askQuestion("Mensaje a enviar (o 'salir' para terminar): ");
        if (msg.toLowerCase() === 'salir') {
            console.log("Saliendo...");
            break;
        }

        const algo_raw = await askQuestion("Algoritmo (Hamming/Fletcher/CRC): ")
        const algo = algo_raw.toLowerCase();
        
        if (!algorithms[algo]) {
            console.error("Algoritmo no válido. Por favor, intente de nuevo.");
            continue;
        }

        const prob  = 0.001;
        const {binMsg, encoded, noisy} = processInput(p=prob, asciiMsg=msg, algo)

        // Crea una nueva conexión TCP
        const client = new net.Socket();
        client.connect(5000, '127.0.0.1', () => {
            // Envía la trama codificada y ruidosa al servidor
            client.write(JSON.stringify({ algo, trama: noisy }));
            console.log("Enviado:", noisy);
            client.end(); // Cierra la conexión después de enviar
        });

        // Maneja errores de conexión
        client.on('error', (err) => {
            console.error('Error de conexión:', err.message);
        });

        // Espera a que la conexión se cierre para continuar con la siguiente pregunta
        await new Promise(resolve => client.on('close', resolve));
        console.log("\n--- Listo para enviar otro mensaje ---\n");
    }
    rl.close(); // Cierra la interfaz readline al salir del bucle
}

async function runTest(totalMessages) {
    const probs = [0.001, 0.005, 0.01];
    const algoNames = Object.keys(algorithms);
    const msgsPerAlgo = Math.floor(totalMessages / algoNames.length);

    const csvHeader = "NumMensaje,Algoritmo,MensajeOriginalASCII,LargoOriginalASCII,MensajeBinario,LargoBinario,MensajeCodificado,LargoCodificado,MensajeEnviado,NoiseProb,BitsFlippeados\n";
    fs.writeFileSync('client_report.csv', csvHeader);

    let msgCounter = 1;

    for (const algo of algoNames) {
        const perProb = Math.floor(msgsPerAlgo / probs.length);
        for (const p of probs) {
            for (let i = 0; i < perProb; i++) {
                
                const asciiMsg = randomAsciiString(5 + Math.floor(Math.random() * 11)); // 5–15 chars
                const {binMsg, encoded, noisy, bitsFlipped} = processInput(p, asciiMsg, algo);

                // Guardar en CSV
                fs.appendFileSync('client_report.csv',
                    `${msgCounter},${algo},${asciiMsg},${asciiMsg.length},${binMsg},${binMsg.length},${encoded},${encoded.length},${noisy},${p},${bitsFlipped}\n`
                );

                // Enviar al servidor con ID - Envuelto en una promesa para poder usar await
                await new Promise((resolve, reject) => { // Usar await con una promesa
                    const client = new net.Socket();
                    client.connect(5000, '127.0.0.1', () => {
                        client.write(JSON.stringify({
                            NumMensaje: msgCounter,
                            algo,
                            trama: noisy
                        }));
                        client.end();
                    });

                    // Resuelve la promesa cuando la conexión se cierre (éxito)
                    client.on('close', () => {
                        resolve();
                    });

                    // Rechaza la promesa si hay un error de conexión
                    client.on('error', (err) => {
                        console.error(`Error al enviar mensaje ${msgCounter} (${algo}, prob=${p}):`, err.message);
                        reject(err); // Rechaa para que await capture el error
                    });
                });

                console.log(`Mensaje ${msgCounter} enviado (${algo}, prob=${p}).`); // Confirmación de envío
                msgCounter++;
            }
        }
    }
    console.log(`\n¡Test de ${totalMessages} mensajes completado!`);
}

if (process.argv[2] === '--test') {
    const total = parseInt(process.argv[3] || '100', 10);
    runTest(total);
} else {
    startSending()
};

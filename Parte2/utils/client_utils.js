// Función auxiliar para convertir ASCII a binario
function asciiToBinary(str) {
    console.log("Convirtiendo mensaje a binario:");
    const binaryStr = str.split('')
        .map(c => c.charCodeAt(0).toString(2).padStart(8, '0'))
        .join('');
    console.log(`${str} → ${binaryStr}\n`);
    return binaryStr;
}

// Función auxiliar para aplicar ruido
function applyNoise(binaryStr, errorProb) {
    return binaryStr.split('').map(bit => {
        if (Math.random() < errorProb) return bit === '0' ? '1' : '0';
        return bit;
    }).join('');
}


// Código para TESTS

function randomAsciiString(length) {
    let result = '';
    for (let i = 0; i < length; i++) {
        result += String.fromCharCode(97 + Math.floor(Math.random() * 26)); // letras minúsculas
    }
    return result;
}





export { asciiToBinary, applyNoise, randomAsciiString}
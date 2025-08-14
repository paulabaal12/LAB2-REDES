# Laboratorio 2 - Parte 2

En la parte 1 se implementaron los siguientes algoritmos:
* **Hamming Code:** Corrección
* **CRC-32:** Detección
* **Fletcher Checksum:** Detección

Los scripts se realizaron en distintos lenguajes:
- **Encoder:** ``Python``
- **Decoder:** ``JavaScript``

## Objetivos:
- Comprender el funcionamiento de un modelo de capas y sus servicios
- Implementar sockets para la transmisión de información
- Experimentar la transmisión de información expuesta a un canal no confiable
- Analizar el funcionamiento de los esquemas de detección y corrección

## Desarrollo:
En la primera parte del laboratorio se implementaron tres algoritmos, dos de **detección** y uno de **corrección**. En esta segunda parte se desarrollará una aplicación para la transmisión y recepción de mensajes, en base a una arquitectura de capas con distintos servicios.

## Arquitectura de capas
Descripción de los servicios:
1. **APLICACIÓN:**
    - Solicitar mensaje: solicita el texto a enviar al emisor. También solicita el algoritmo a utilizar para comprobar la integridad.
    - Mostrar mensaje: muestra el mensaje al receptor (sin errores). Si se detectaron errores y no fue posible corregirlos, se debe indicar con un mensaje de error.
2. **PRESENTACIÓN:**
    - Codificar mensaje: codifica cada caracter individual en ASCII binario. Por ejemplo, para el carácter A el código binario ASCII es 01000001.
    - Decodificar mensaje: si no se detectan errores, se debe decodificar el ASCII binario a los caracteres correspondientes. Si se detecta algún error, se debe indicar a la capa de aplicación.
3. **ENLACE:**
    - Calcular integridad: utilizando el algoritmo indicado en el servicio solicitar_mensaje, calcular la información de integridad. Concatenar la información al mensaje en binario original.
    - Verificar integridad: el algoritmo seleccionado debe calcular la información del lado del receptor y compararla contra la proporcionada por el emisor para detectar posibles errores. Debe indicar esto a la capa de presentación. Aquí es donde se deben integrar los algoritmos implementados en la primera parte del laboratorio.
    - Corregir mensaje: si el algoritmo tiene la capacidad de corregir los errores detectados debe corregirlos.
4. **RUIDO:**
    - Aplicar ruido: el ruido no es una capa como tal, pero a fin de simular posibles interferencias se tratará como una capa del lado del emisor, y se aplicará ruido a la trama proporcionada por la capa de enlace. La forma de determinar si cada bit se voltea (bit = !bit) se basará en cierta probabilidad expresada en errores por bits transmitidos (por ejemplo, 1/100=0.01 es un error por cada 100 bits). Note que ¡los bits de paridad también son propensos al ruido!
5. **TRANSMISIÓN:**
    - Enviar información: envía la trama de información a través de sockets mediante el puerto elegido.
    - Recibir información: recibe la trama de información a través de sockets mediante el puerto elegido. El receptor siempre debe estar “escuchando” en el puerto elegido a la espera de recibir datos (i.e.: a modo “server” y el emisor a modo “client”).

La aplicación del lado del emisor está implementada en `JavaScript` y del receptor está implementada en `Python`.

## Pruebas
Utilizando los algoritmos implementados realizar varias pruebas (10k, 100k+) de envío y recepción, donde se logre evidenciar el funcionamiento de los algoritmos.

Busque automatizar el proceso de pruebas, análisis estadístico y despliegue de gráficas. Para estas pruebas cada grupo deberá de elegir cómo las realizará y generar gráficas que reflejen estos datos y respalden su discusión y conclusiones. La cantidad y contenido de las gráficas queda a discreción del grupo, no obstante, deben de ser realizadas variando el **tamaño de las cadenas enviadas**, la **probabilidad de error**, el algoritmo utilizado y la **redundancia/taza de código** para que el algoritmo sea efectivo (ej: r bits de paridad, en Hamming, o taza 2:1, 3:1, r:1 en convolucional).

Algunas preguntas que pueden ayudar a la discusión son:
- ¿Qué algoritmo tuvo un mejor funcionamiento y por qué?
- ¿Qué algoritmo es más flexible para aceptar mayores tasas de errores y por qué?
- ¿Cuándo es mejor utilizar un algoritmo de detección de errores en lugar de uno de corrección de errores y por qué?
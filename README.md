# LAB2-REDES

## Parte 1: Fletcher Checksum

### Codificación
Para codificar los mensajes y generar los archivos con checksum:

```bash
cd Parte1/FletcherChecksum
node encoder.js in/msg1.txt in/msg2.txt in/msg3.txt --block-size=16 --verbose
```

Los archivos generados estarán en la carpeta `out/`.

### Decodificación y verificación
Para verificar los mensajes codificados:

```bash
cd Parte1/FletcherChecksum
python3 decoder.py out/msg1_fletcher16.txt out/msg2_fletcher16.txt out/msg3_fletcher16.txt --block-size=16
```

Esto mostrará si los checksums son correctos y recuperará el mensaje original.
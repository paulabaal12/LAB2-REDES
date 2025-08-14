# Aquí estaría el código que genera los reportes de pruebas basándose en los archivos generados:
# - client_report.csv
#   NumMensaje,Algoritmo,MensajeOriginalASCII,LargoOriginalASCII,MensajeBinario,LargoBinario,MensajeCodificado,LargoCodificado,MensajeEnviado,NoiseProb,BitsFlippeados
# - errors.csv: En caso de haber recibido y decodificado un mensaje erróneo, en este archivo se guardará lo siguiente:
#   NumMensaje,Real,Falso
# - server_report.csv: Al recibir un mensaje y que Hamming detecte un error, se guardará el éxito o fallo de la corrección
#   NumMensaje,Algoritmo,MensajeRecibido,Fix,Success

# Ideas de reportes:
# - Comparación de mensajes enviados sin y con errores por ruido, dividido por algoritmos
# - Por algoritmos y largo del mensaje binario, porcentaje de mensajes corregidos exitosamente
# - Tasa de éxito para cada algoritmo
# HoneySSH

## Descripción breve

Este script es un honeypot casero construido casi desde cero. Este honeypot, hecho en Python, lo que hace es simular un servicio en SSH, en el puerto 22, que tiene un diccionario de respuestas falsas, que entrega cuando se le envía algún comando (por ejemplo, whoami). Recoge logs de varios tipos: qué comandos ha probado el atacante, la IP, la localización geográfica, la fecha, la hora, el número de intentos, la duración de las sesiones y los errores que se dan en él. 


## Requisitos
- Python 3.x
- Librerías:
  - socket
  - datetime
  - requests
  - os
  - csv
  - random
  - uuid
  - hashlib
  - mimetypes
  - concurrent.futures
  - threading
  - logging
  - paramiko (incluyendo RSA)


## Uso

```bash 
# Clonar el repositorio
git clone https://github.com/Destrek/honeySSH.git

# Entrar en la carpeta
cd honeySSH

# Ejecutar el honeypot
python3 honeySSH.py



Estructura:

honeySSH/
├── src/             
├── graphs/     
├── docs/ 
├── Devlog.md/      
├─ README.md   ─
└── LICENSE     




Resultados:


![Gráfico de usuarios](top usuarios más intentados.png)

![Honeypot SSH final en funcionamiento](funcionamientofinal1-1-1.jpg)



Licencia:

MIT

```

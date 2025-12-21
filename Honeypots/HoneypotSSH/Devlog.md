Honeypot casero
Versión:  1.0  
Fecha: 24/08/2025 - 1/11/2025
Autor: Jorge V. N. (Destrek)

Descripción breve

Este script es un honeypot casero construido casi desde cero. Es muy sencillo. Debo decir, no obstante, antes de nada, que soy nuevo en el campo de la informática. Escribo esto para compartir mi primer experimento con los demás. Es algo muy sencillo, quizás muy simple, pero, bueno, me ha gustado el hecho de probarlo y ponerme a trabajar con él. 

Este honeypot, hecho en Python, lo que hace es simular un servicio en SSH, en el puerto 2222, que tiene un diccionario de respuestas falsas, que entrega cuando se le envía algún comando (por ejemplo, whoami). Recoge logs de varios tipos: qué comandos ha probado el atacante, la IP, la localización geográfica, la fecha, la hora, el número de intentos, la duración de las sesiones y los errores que se dan en él. 


 Objetivo y contexto

- Ha sido un experimento interesante para ver cómo funciona tanto el hecho de atacarlo como el hecho de ver, desde el otro lado, como defensor, cómo recoge datos de los que interactúan con él.

- Para un principiante, como yo, creo que puede servir para montar un primer laboratorio en el que probar tanto reconocimiento como ataque en un entorno controlado.

 Puedes montar dos máquinas virtuales:
 
  Atacante: para ejecutar comandos y practicar pentesting básico (nmap, por ejemplo)
   
  Defensor: donde puedes escuchar en el puerto abierto simulado, porque no tiene ningún servicio real, y observar cómo recoge logs de lo que sucede y te da información sobre lo que el atacante ha intentado hacer. 

Las puedes conectar mediante una red NAT (yo la he creado aposta en VMWare) y probar variedad de cosas. Con ello, como me ha pasado a mí, practicas un poco de todo y te familiarizas con cómo funcionan las redes, los puertos y la recolección de logs. 

- La idea me ha venido de dos sitios: 
1. De que ya conocía los honeypots antes de empezar en este mundillo, pero nunca había construido ninguno, ni usado, y no sabía realmente cómo funcionaban o qué hacían, más allá de servir de "trampa" o "señuelo".

2. De la curiosidad que sentía por saber cómo era uno por dentro. Sé que en materia de honeypots puede hacerse mucho, pero, en mi caso, me he propuesto algo muy sencillo para aprender y observar.  



Requisitos Previos

- Python 3.X
- Librerías necesarias (socket, datetime, requests, time)
- Entorno de pruebas (v.gr., máquina virtual con Linux, pero valdría Docker)



Uso básico

Encender el honeypot en una máquina virtual y desde otra probar comandos.



Estado del proyecto

Versión 1.0 terminada.

Ejemplos de uso

![Prueba del Honeypot](funcionamiento1-1.png)


![SalidahoneypotSSH](funcionamientofinal1-1.jpg)


Evolución del proyecto

El proyecto lo empecé con un pequeño script que me hizo la IA. El script era un honeypot de telnet de 10 líneas que apenas abría un socket y recogía unos pocos logs de las conexiones entrantes. Las escribía en un archivo .log. No tenía clases ni funciones. Luego le añadí funciones, como por ejemplo la de geolocalización, que puede verse en el propio script final de Python. Luego seguí poco a poco añadiendo funciones, las cuales añadían su propio logger. El resultado de esto fue que los logs, lejos de estar unificados, iban cada uno por un sitio distinto, lo cual provocó problemas en el archivo de logs. Llegó un momento en que los logs ya ni siquiera se guardaban, aunque el honeypot funcionara perfectamente.

Llegué a un punto en donde mi código estaba tan disperso y era tan caótico, que tenía tres tipos de logs antes de las funciones y después y cada función su propio tipo de logs. El resultado de esto fue que cuando intentaba usar el honeypot, aunque funcionara, no recogía logs. Era como si no funcionara. Por ese motivo, tuve que crear dos clases: una, la principal, para el honeypot con su socket y las funciones principales (ahora métodos), y otra sólo para los logs, centralizándolos y ordenándolos de modo fijo por el tipo de datos que quería recoger. Como se trataba de un honeypot sencillo que sólo escuchaba en SSH, pero que no simulaba nada en sí, no era ningún servicio real, no hacía falta que fueran muchos parámetros. Así que dentro de la clase HoneyLogger tuve que crear su __init__ correspondiente y debajo de él un diccionario para los logs, que quedaba así: 
"
def crear_evento(self, PORT, IP, ubicacion, duracion, frecuencia, credencial):
      evento = {
         "timestamp": datetime.now().isoformat(),
         "Port": PORT,
         "IP": IP,
         "ubicación": geolocalizar,
         "Duración": duracion,
         "Frecuencia": frecuencia,
         "Credencial": credencial
      }
      return evento", en un método propio.

A eso tuve que añadirle otro diccionario en el init de la clase: 
self.campos = [
            "timestamp", "ip", "port", "ubicacion",
            "duracion", "frecuencia", "credencial",
            "asn", "reverse_dns"
        ]

El siguiente método fue guardar el evento creado y estructurado del método anterior. 

Ahora quedaba refactorizar la clase anterior, principal, donde tenía el socket con todo el proceso de interacción con el exterior. Este bloque: 
"with open("credenciales.log", "a") as f:
                     f.write(f"[{datetime.now()}] {ip} -> Usuario: {usuario} | Pass: {contrasena}\n")
                     # Al salir del bucle (después del break)
                     inicio_sesion = datetime.now()
                     duracion = datetime.now() - inicio_sesion
                     with open("duracion_sesiones.log", "a") as f:
                        f.write(f"[{datetime.now()}] {ip} -> Duración: {duracion.total_seconds()} segundos\n")
                        intentos_por_ip = {}
                        # Contar intento por IP
                        intentos_por_ip[ip] = intentos_por_ip.get(ip, 0) + 1
                        with open("frecuencia_intentos.log", "a") as f:
                         f.write(f"[{datetime.now()}] {ip} -> Intentos acumulados: {intentos_por_ip[ip]}\n")
                else:
                        # Procesar comando normal y responder desde el diccionario
                        comando = datos.lower()
                        log_comando(comando)  # si tienes esta función

                        respuesta = RESPUESTAS.get(
                            comando,
                            f"bash: {comando}: command not found\n"
                        )

                        conn.sendall(respuesta.encode())
        except Exception as e:
                     # Registrar el error y salir del bucle
         log_error(e)
         break", tuve que borrarlo entero para crear uno más pequeño que creara un evento y ese evento pudiera pasarse a la clase HoneyLogger para que ella hiciera todo el trabajo a ese respecto, en campos y en información de interés.       

Cuando me puse a adaptar la función principal que usaba (un pequeño socket para escuchar y recibir conexiones de otros), me di cuenta que tal y como estaba no iba a servir tampoco. Así que tuve que desdoblarlo en dos métodos dentro de la función: "def iniciar" y "def manejar_conexion", con funciones específicas para cada método. Uno se encarga de iniciar la conexión y otro de manejarla y de recoger los datos que están establecidos en diccionario de aquel que se conecte, incluida la ubicación geográfica, que era una pequeña función que tenía y que he podido adaptar en la refactorización. 
El método manejar_conexion, a su vez, remite los datos en forma de log a la clase más abajo que se encarga de todo ello, la de HoneyLogger. Y así entre las clases y sus métodos deberían actuar de modo conjunto, cada una con su tarea. 

Sobra decir que tuve que crear un __init__ para la clase Honeypot, que quedó así: 
"def __init__(self, host, port, logger):
  self.host = host
  self.port = port
  self.logger = logger
  self.intentos_por_ip = {}
  "

Así, la clase Honeypot tenía 3 métodos: geolocalizar, iniciar y manejar_conexion. HoneyLogger 2: crear_evento y guardar_evento, con logs en archivo .CSV aparte.   

Al actualizar el método de geolocalización de la clase Honeypot, éste dejó de iniciarse y de funcionar. Con lo cual, no se podía hacer nada con la otra VM en cuestión de pruebas. Y lo peor es que el error no me aparecía por ninguna parte ni sabía cuál era. 

Cuando actualizo y mejoro el método, resulta que el honeypot no me deja enviar más que un comando. No acepta más y, por ende, no recoge logs, porque sólo acepta y responde a una única cosa. ¿Dónde estaba el problema? Presumiblemente en el bucle, antes de empezar con "While True" en el método manejar_conexion. El problema estaba en esta línea, que debería haberla cambiado: "conn.sendall(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5\r\n")". La cambié por esta: "conn.sendall(self.prompt.encode())", y ya dejaba enviar comandos que recibían respuestas falsas del diccionario. 

Un problema menos. Pero aún quedaba otro: los logs seguían sin registrarse en el archivo .csv. Así que tuve que volver a pensar qué fallaba. Y me ha costado bastante. Haciendo pequeñas correciones en el diccionario del método crear_evento y del de manejar_conexion parece que lo he solucionado. Los he homegeneizado, porque los tenía de un modo en un lado y de otro modo en otro lado. Además, me faltaba alguno de los parámetros en el init de HoneyLogger. 

Después de conseguir que funcionara y creara el archivo .csv, me puse a mejorar el realismo del honeypot ajustando el sistema operativo, para que lo ofreciera vinculado al usuario elegido aleatoriamente (según está establecido en el diccionario). 

Una de las cosas que añadí fue, ya no sólo recoger credenciales concretas de intentos de sesión, sino simular que se podía iniciar sesión (aunque no haya nada detrás) hasta tres veces y luego cortar la sesión del atacante: "if intentos < 3:
               time.sleep(random.uniform(0.8, 1.5))
               conn.sendall(b"Permission denied, please try again. \n")
            else: 
               conn.sendall(b"Permission denied (publickey, password) \n")
               break
            continue"

Luego añadir pequeños retardos a la hora de hacer cosas como ofrecer el banner del sistema operativo del disfraz, a la hora de intentar iniciar sesión y a la hora de escribir comandos. Eso lo hice con: "import time 

time sleep(1)".

En cada caso usé una aleatorización de tiempos de respuesta concretos para hacerlo diferente cada vez y más realista. El primero así: "conn.sendall(f"{self.sistema}\n".encode("utf-8"))
      time.sleep(random.uniform(0.2, 0.5))      
      conn.sendall(self.prompt.encode())".

El segundo así: "if intentos < 3:
               time.sleep(random.uniform(0.8, 1.5))
               conn.sendall(b"Permission denied, please try again. \n")".

El tercero así: "respuesta = RESPUESTAS.get(datos, f"bash: {datos} command not found")
         conn.sendall(f"{respuesta}\n{self.prompt}".encode())
         time.sleep(random.uniform(0.2, 0.6))". 

Más tarde, cambié las referencias del diccionario de respuestas falsas, que siempre decían "Kali" por Placeholder, que tuve que añadir como respuesta dentro del método manejar_conexion para que lo ofreciera en consonancia con el disfraz que elige el script automáticamente. Y concordaban. Cada disfraz usaba el sistema operativo que tenía asignado en el diccionario, así que funcionaba perfectamente. 

También cambié los mensajes de error cuando se intentaba iniciar sesión en el propio honeypot. Empecé con tres: "Permission denied, please try again", "Access denied, try again" y "Authentication failed". Y los aleatoricé. Y funcionaban. Funcionaban bien. 

Luego pensé en mejorarlo e intentar crear un bucle de inicios de sesión no tan aleatorio y sí más real con respecto a un sistema real.

Ya funcionaba bastante bien el honeypot, pero seguía sin convencerme. Quería que se pudiera intentar una conexión real a un SSH fingido y que dejara creer que podías iniciar sesión y meterte dentro para escribir comandos e intentar descargar o meter cosas. Así que tenía que darle una vuelta de tuerca a lo que había hecho y simular mejor el SSH, que es lo que llevo intentando desde que empecé con este honeypot. El telnet funcionaba, aunque no te hacía creer que entrabas, pero el SSH es en lo que debía centrarme. 

Por ejemplo, para mayor realismo era mejor cambiar el banner que usaba el honeypot por banners específicos de cada sistema operativo de cada disfraz creado. Así lo tenía antes: "Banners = f"SSH-2.0-OpenSSH_8.2p1 {sistema}"", siempre el mismo, aunque cambiara el sistema concreto por el placeholder. Ahora era: "Banners = {"Ubuntu 20.04": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
           "Debian 11": "SSH-2.0-OpenSSH_8.4p1 Debian-5+deb11u1",
           "CentOS 7": "SSH-2.0-OpenSSH_7.4p1 RedHat-10",
           "Kali Linux": "SSH-2.0-OpenSSH_9.2p1 Debian-2",
           "Arch Linux": "SSH-2.0-OpenSSH_9.6p1",
           "Ubuntu 22.04": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.10"

}". 

Para hacer lo que quería hacer tenía que hacer bastantes cambios en los métodos de mi honeypot, sobre todo en el de manejar_conexion. Eventualmente, incluso definir métodos nuevos y diferentes para poder establecer el sistema de login falso. Para empezar, usar un diccionario de estado con parámetros fijos y predefinidos: "estado = {"fase": "login",
                "start_time": datetime.now(),
                "ip_remota": ip,
                "disfraz": self.sistema,
                "hostname": self.hostname,
                "geo": self.geolocalizar(ip),
                "reverse_dns": reverse_dns,
                "usuario": None,
                "intentos": 0,
                "aceptado": False,
      }". 
Pero también otro de credenciales que iba a aceptar para dejar entrar en el SSH fingido: "credenciales_aceptadas = {
         "root": {"1234", "toor"},
         "admin": {"admin"}
      }".

Todo ello acompañado del banner concreto apropiado para cada sistema operativo y de registro de logs.  Además, para separar lógica, tuve que crear un nuevo método dentro de la clase Honeypot para que se encargara del proceso de inicio de sesión: "def procesar_login(self, conn, raw, estado):"
Pero también otros dos métodos: "def extraer_credenciales(linea: str):      
      linea = (linea or "").strip()
      if not linea:
         return None, None
      if ":" in linea:
         u, p = linea.split(":", 1)  
         return u.strip(), p.strip()
      partes = linea.split()
      if len(partes) == 2:
         return partes[0].strip(), partes[1].strip()"
y
"def credencial_aceptada(user: str, pwd:str) -> bool:
      return user in credenciales_aceptadas and pwd in credenciales_aceptadas[user]".

Para recrear un ambiente realista después de iniciar sesión en el honeypot de forma fingida, tuve que que crear un pequeño shell. Así debía hacerlo: "def procesar_shell(self, conn, raw, estado):". 

Tras hacer la shell falsa y darle apariencia de sistema real, tuve errores de indentación y con cierta parte del honeypot, esta: "def extraer_credenciales(self, linea: str):      
      linea = (linea or "").strip()
      if not linea:
         return None, None
      if ":" in linea:
         u, p = linea.split(":", 1)  
         return u.strip(), p.strip()
      partes = linea.split()
      if len(partes) == 2:
         return partes[0].strip(), partes[1].strip()
      return None, None". 
Fue algo tan tonto como que se me olvidó incluir el self al principio del método. 

Otro error tonto que tenía era que en el método de procesar_shell tenía mal escrita la invocación del diccionario de Respuestas falsas del principio del archivo. Cuando solucioné ambas cosas, funcionó perfectamente. 

Funcionando así y teniendo lo que tenía, decidí no tocar el código más, porque los errores no han sido pocos y me he pasado horas y días sin saber cómo solucionarlos. Los últimos arreglos que acabo de mencionar los conseguí probando por probar, porque me daba error el orden e indentación de un método y palabras faltantes o sin adaptación. 

Así que me dediqué a pequeñas funcionalidades extra para simular más realismo. En concreto añadí un pequeño efecto de last login para cuando entras en el sistema falso. Con tres líneas en el método de procesar_login lo hice. Primero hice una para la fecha de ahora, pero no me convencía. Así que decidí coger la fecha actual y con timedelta restarle un par de días, horas y minutos para que no quedara tan raro: 
" last_time = datetime.now() - timedelta(days=2, hours=3, minutes=17)
        last_login = f"last Login: {last_time.strftime('%a %b %d %H:%M:%S %Y')} from {estado['ip_remota']}\n"
        conn.sendall(last_login.encode())". 
Con esto, ya funcionó perfectamente. 

Otro pequeño detalle que se podía incluir era un "Message of the Day" después de este last login para simular más aún un sistema real. Poca cosa, porque estaba acabando ya el honeypot y no quería hacer grandes cambios.

El Message of the Day (MOTD) lo introduje con un diccionario dentro de la clase principal de Honeypot. Pero como me daba problemas a la hora de que Python me lo reconociera tal y como lo quería usar, tuve que añadir: "dict[str, list[str]]", y los valores del diccionario con []. Tuve que añadir también dos pequeñas líneas en el método de procesar_login. 

Y funcionó pero no conseguía que hubiera una línea en blanco entre Last login y el comienzo del MOTD. 

Después me puse a trabajar en el usuario. Nada más entrar debía ser "admin" y tras acceder a la shell cambiar a "root", para simular que se escalan privilegios. Tuve que cambiar la lógica y añadir un campo nuevo a la clase de logs y a los logs que recogía en la clase Honeypot, en procesar_login, pero volvió a darme error. Otra vez dejó de funcionar. Así que tenía otro fallo, no visible a simple vista, porque el código estaba bien escrito, que rompía casi todo. Y me tocaba arreglarlo. 

Al hacer los cambios requeridos, tuve que borrar el bucle anterior y tuve que volver a adaptar los logs, tanto los que se guardaban en manejar_conexion como los de la clase Honeylogger. Aunque, eso sí, ahora podía registrar intentos de contraseñas y usuarios fallidos por separado, cosa que antes no era posible.

Cuando lo probé, funcionaba, porque te pedía nombre de usuario y más tarde la contraseña. Pero cuando lo probaba se cerraba la conexión. Así que me tocaba solucionarlo. 


Me volví bastante loco con el arreglo del honeypot. Cambié y adapté pequeñas cosas en todos los métodos principales de la clase Honeypot. Ni aun así funcionaba. Pero al ejecutar el honeypot y probarlo, pude ver en los Debug cuáles eran los problemas. Uno de ellos era: "'set' object has no attribute 'get'". El logger intentaba coger un set a través de get que no podía, en lugar de un diccionario, y que rompía todo el flujo. El otro que faltaban campos añadidos en los loggers de los métodos de la clase honeypot que se me había pasado incluir a los campos del init de HoneyLogger para que los pudiera escribir y guardar. 

Después de esto y de varios días probando cosas, por fin funciona. Tanto iniciando sesión como admin, como si lo haces como root. 

Ahora, sólo quería añadir pequeñas cosas a nivel logs y las dos últimas funcionalidades de este honeypot: threading y un método para extraer scripts de atacantes, pasarlos a .txt y luego poder estudiarlos y extraer metadatos y hashes de ellos. 

Lo primero, asignar un id de sesión para cada atacante en su actividad. Para ello, importé la librería "uuid" y añadí al diccionario de "estado" en el método manejar_conexion esta línea al principio: ""session_id": self.generar_identificacion()". 

Después creé el último método del honeypot: "def capturar_payload(self, estado, contenido:bytes, nombre_sugerido="payloads")". Usé el sha256 con la librería "hash" para calcular y extraer los hashes de los payloads que iba a capturar. 

Hice las adaptaciones pertinentes en el método procesar_shell para que cuando detectara que alguien intentaba inyectar o ejecutar algo dentro del honeypot, se lo pasara a estye método, lo extrayera y sacara datos. Lo puse debajo de la detección y respuesta de comandos. No tuve que tocar nada de la lógica que ya había escrito. Fue simplemente añadir en varias partes lo que iba a capturar: cat, wget y curl. Y también las urls de los binarios que intentaran ejecutar. 

Después, añadí los campos nuevos en HoneyLogger(archivo", "hash", "tamano", "tipo_payload", "session_id", "echo_script", "cat_script", "payload_executable", "payload_url"). Pero tenía desordenados los campos de "crear_evento", así que me puse a ordenarlos de otro modo, de un modo donde estuvieran más relacionados entre sí.

Los logs en el archivo .CSV se escribían raramente, con anchos de columna desproporcionados y sin nombres para las columnas nuevas. Hasta que se me ocurrió borrar el archivo y dejar que se generara de nuevo con el orden bien establecido y con todos los campos desde el principio. Después de probarlo, encontré todos los campos ordenados con todas sus columnas con su nombre y todos los datos ordenados. El orden, por fin, era perfecto. Un ejemplo es este: 
"timestamp,ip,port,ubicacion,duracion,frecuencia,credencial,isp,asn,reverse_dns,hostname_simulado,sistema_simulado,evento,usuario,password,comando,usuario_asignado,usuario_intentado,password_intentada,archivo,hash,tamano,tipo_payload,session_id,echo_script,cat_script,payload_executable,payload_url
2025-10-05T20:54:17.030854,192.168.2.128,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,login_try,admin,admin,N/A,admin,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A
" (nótese que todos los N/A se deben a que las pruebas las hago en NAT). 

Pero la tabla como tal con los campos más importantes es la siguiente:

| Campo              | Descripción                                      | Ejemplo                          |
|--------------------|--------------------------------------------------|----------------------------------|
| timestamp          | Fecha y hora del evento en ISO 8601              | 2025-10-05T20:54:17              |
| ip                 | Dirección IP del atacante                        | 192.168.2.128                    |
| port               | Puerto de conexión                               | 22                               |
| evento             | Tipo de evento registrado                        | login_try / cmd_exec / payload   |
| usuario_intentado  | Usuario que el atacante intentó usar             | admin                            |
| password_intentada | Contraseña probada por el atacante               | 123456                           |
| comando            | Comando ejecutado por el atacante                | ls -la                           |
| archivo            | Nombre del archivo capturado como payload        | prueba_honeypot.sh               |
| hash               | Hash SHA256 del payload                          | a66a15f2104b1ef237fffb7797aa58…  |
| tipo_payload       | Clasificación del payload (script, binario, etc.)| script                           |
| session_id         | Identificador único de la sesión                 | 4f391b7f-d99b-4125-9aec-…        |

Como detalle final, me propuse añadirle threading al honeypot. Lo cierto es que no lo había hecho nunca, pero gracias a mi estructura en clases y métodos y a que tenía el socket dividido en funciones a cumplir, sólo tuve que coger el método de iniciar(self) y añadírselo. Tuve que escribir unas pocas líneas (después de hacer "import threading"), más o menos 3 o 4. Pero luego vi que lanzaba hilos infinitos y que eso para un honeypot podía ser peligroso, aparte de consumir muchos recursos. Así que me propuse añadir una limitación. La limitación tenía que ser con un pool de hilos. Lo limité a 20 para evitar ataques DoS, aparte de vigilar que hubiera atacantes que pudieran saturar los hilos sin enviar nada, por lo que con un tiempo para cada hilo y una excepción para el socket (except socket.timeout: continue), para que no se quede colgado, los hilos se producen con mayor naturalidad y robustez y si no reciben ninguna información pueden cerrarse y el honeypot puede seguir escuchando sin problemas. 

El problema que podría haber ahora, con este cambio, es que los logs se mezclaran o no fueran escritos en orden, porque podía haber ya varios hilos al mismo tiempo. Para prevenirlos antes de que sucedieran, usé la librería de "logging". Esto lo solucioné usando un "lock" tanto en el init como en el método de guardar_evento. En init con: "self.lock = threading.Lock()". En def guardar_evento con: "with self.lock:".

En el método de manejar_conexión decidí, además, poner un contador de conexiones para ver luego en los logs cuántas conexiones activas había en un momento dado al mismo tiempo. Me parecía un dato curioso que quería recoger. Tuve que retocar el método un poco, pero nada de lo principal. Lo hice con: "with self.lock_conexiones:
          self.conexiones_activas +=1
          activas = self.conexiones_activas". 
También en los logs añadí un campo nuevo a recoger: "self.logger.crear_evento({
          "evento": "nueva_conexion",
          "ip": addr[0],
          "port": addr[1],
          "conexiones_activas": activas,
          "thread": threading.current_thread().name
      })".

Para seguir con el honeypot, tenía que solucionar el problema con diversas respuestas falsas que se daban a ciertos comandos introducidos. Tanto las f-strings como los placeholders fallaban y siempre devolvían "Kali Linux" en lugar del disfraz elegido. Se producía, por tanto, una incoherencia que restaba verosimilitud. Así que me fijé en la parte donde se procesaban los comandos, en concreto, en el método "procesar_shell" y me fijé en: " if comando_norm in RESPUESTAS:
       salida = RESPUESTAS[comando_norm]
       if isinstance(salida, (list, tuple)):
         for linea in salida:
            conn.sendall(f"{linea}\n".encode())
       else:
         conn.sendall(f"{salida}\n".encode())
      else:
        time.sleep(random.uniform(0.2, 0.6))
        conn.sendall(f"bash: {comando_norm}: command not found\n".encode())".

El problema aquí está en que no procesa f-strings ni placeholders. Así que tuve que cambiar esta parte, adaptarla para que las respuestas falsas fueran más adaptativas y realistas. 
Después de "salida = RESPUESTAS[comando_norm]" añadí este pequeño bloque: "if isinstance(salida, str):
           salida = salida.format(
               HostName = estado.get("HostName"),
               sistema = estado.get("sistema")
           )", para usar format y que ya pudiera usar placeholders dentro del diccionario de respuestas falsas. 

El problema es que la elección de disfraces, sistema, MOTD, etc., se hacían a nivel de instancia, del init, y no del método, centralizado en manejar_conexión. Por tanto tuve que mover a [estado] todos estos parámetros y realizar ciertos cambios más profundos de lo que yo creía. 

Después de estar cambiando y probando cosas, parece que lo que más me fallaba era que no había cambiado la variable del HostName (que tantos problemas me estaba dando) por la del estado.get correcta. Bien escrita esa parte del .format() quedaba así: "if isinstance(salida, str):
           salida = salida.format(
               HostName = estado.get("hostname"),
               sistema = estado.get("sistema")
           )".

Por si esto fuera poco, me di cuenta que la recogida de logs estaba bien preparada con muchos campos en la clase HoneyLogger, pero esos campos, que estaban ya preparados para ser recogidos, no los estaba recogiendo porque no los había incluido de modo sistemático en los loggers individuales de cada método de los que se encargaban de la conexión y el bucle del socket: "manejar_conexion", "procesar_login" y "procesar_shell". En todos ellos, incluí los campos: "hostname_simulado", "sistema_simulado", "reverse_dns" y "geo". Ahora se recogían de modo individual en cada log del archivo .CSV y no hacía falta mirar a otros para sacar información. Cada línea da la información precisa y ya puede relacionarse entre sí.

Ahora que está todo funcionando bien, es el momento de cambiar el transporte, el protocolo, que es telnet básico por el protocolo SSH real. No se requiere para imitarlo y engañar implementarlo entero y tal cual. Basta con la librería paramiko y adaptar el socket actual aparte de usar una clave host (RSA). Después, el ServerInterface para la autenticación. Más tarde, el servidor SSH como tal. Si todo va bien, podrá hacerse conexión directa con SSH@IP e introducirse en la falsa shell. 

Para conseguirlo, creé una clase nueva que enganchar luego al socket de Honeypot. Se encargaría de la interfaz en Paramiko y de aceptar o no conexiones según si iniciaban sesión con los usuarios y contraseñas de mi diccionario de credenciales_aceptadas o no. Si no inician sesión según he establecido, se corta la conexión y se les impide acceder a la falsa shell. 

El grueso de los cambios, sin embargo, va en la clase honeypot porque hay que cambiar el transporte del socket principal y hacerlo pasar de telnet plano a SSH. Para ello, había que empezar en el método "iniciar", al que añadí esta línea: "s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)". De tal modo que quedaba así: "with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   
     s.bind((self.host, self.port))
     s.listen()
     s.settimeout(10)
     print(f"Honeypot escuchando en {self.host}:{self.port}...")". 

Prácticamente igual que antes.

Ahora hay que adaptar el método "manejar_conexion" para usar el transporte SSH, añadir la clave de mi servidor, instanciarlo a la clase nueva creada recientemente con el logger y el estado inicial, llamar al transporte, esperar a que el cliente abra un canal, pasarle ese canal a la shell falsa y registrar los 
eventos, comandos, payloads, todo, y cerrar con los logs de HoneyLogger en archivo .CSV.

Hecho esto, creé un pequeño método dentro de la clase Honeypot para generar una clave de Host SSH que se genera en un archivo aparte y que es siempre la misma para simular que se trata de un servidor auténtico. Quedó así: "def cargar_o_generar_clave(self, ruta="host_rsa.key"):
     if os.path.exists(ruta):
         print(f"[DEBUG] Cargando clave de host desde {ruta}")
         return RSAKey(filename=ruta)
     else:
         print(f"[DEBUG] No existe ninguna clave de host. Generando una nueva en {ruta}")
         key = RSAKey.generate(2048)
         key.write_private_key_file(ruta)
         return key"

Después había que encargarse de la shell. El método que se ocupa de la shell, de los comandos, de las respuestas falsas, de registrar los datos interesantes que pueden analizarse luego suplantaba o absorbía todas las funciones que ya tenía en el método "procesar_shell", así que decidí mantener este método, pero también crear el de la shell de SSH para que se repartieran el trabajo y aprovechar lo que había construido con anterioridad. Para eso, tenía que adaptar "procesar_shell". 

Al conectar directamente con SSH, el servidor levantado por el honeypot funciona y conecta perfectamente. ¿El problema ahora? De carácter estético. Tanto el MOTD como el prompt y las respuestas falsas se mostraban desordenados y difícilmente legibles. 
Normalizando los saltos de línea conseguí que el MOTD se mostrara perfectamente legible y ordenado. Lo hice en shell_loop: "for linea in estado.get("motd", []):
        chan.send(linea.replace("\n", "\r\n").encode())". 
Así que ahora la cuestión era conseguir lo mismo con el prompt y las respuestas falsas.

Para normalizar las líneas, los bloques de texto y colocar el prompt bien siempre y que sea legible, tuve que crear tres métodos auxiliares, muy pequeños, al principio de la clase Honeypot. Son estos: "def enviar_linea(self, chan, text=""):
    # Enviar una línea completa con CRLF
    chan.send((text.replace("\n", "\r\n") + "\r\n").encode())

 def enviar_bloque(self, chan, text):
    # Enviar un bloque de texto normalizado, sin prompt
    chan.send(text.replace("\n", "\r\n").encode())

 def enviar_prompt(self, chan, prompt):
    # Volver al inicio, limpiar la línea y pintar prompt
    chan.send(("\r\x1b[K" + prompt + " ").encode())".

Luego reemplacé las líneas de "bucle_de_shell" y "procesar_shell" por llamadas a estos métodos. 
Y funcionó perfectamente, o casi. Tanto el MOTD, como el prompt, como las respuestas falsas estaban perfectamente alineadas y se mantenían en su sitio. Ahora parecía una sesión SSH real. 

Para pulir el honeypot, me fijé en los pequeños detalles. Hice que los logs se crearan en una carpeta propia, donde se almacenaran, para poder así tener control sobre los permisos de la misma. El cambio lo logré dentro de HoneyLogger así: "def __init__(self, log_filename="logsHoneypot.csv"):
      os.makedirs("logs", exist_ok=True)
      self.LOG_FILE = os.path.join("logs", log_filename)".

Con la clave SSH del servidor del honeypot hice lo mismo: 

"def cargar_o_generar_clave(self, key_filename="host_rsa.key"):
     key_dir = "keys"
     os.makedirs(key_dir, exist_ok=True)
     key_path = os.path.join(key_dir, key_filename)
     if os.path.exists(key_path):
         print(f"[DEBUG] Cargando clave de host desde {key_path}")
         return RSAKey(filename=key_path)
     else:
         print(f"[DEBUG] No existe ninguna clave de host. Generando una nueva en {key_path}")
         key = RSAKey.generate(2048)
         key.write_private_key_file(key_path)
         return key".

Sustituí "ruta" y puse "key_filename", además de usar "key_path", aparte de verificar que la carpeta realmente estuviera y, que si no, se creara.                

También hice cambios en la clase HoneyLogger para centralizar directorios: "def __init__(self, log_filename="logsHoneypot.csv", key_filename="host_rsa.key"):
      self.LOG_DIR = "logs"
      self.KEY_DIR = "keys"
      self.PAYLOAD_DIR = "payloads"
       
      os.makedirs(self.LOG_DIR, exist_ok=True)
      os.makedirs(self.KEY_DIR, exist_ok=True)
      os.makedirs(self.PAYLOAD_DIR, exist_ok=True)
    
      self.LOG_FILE = os.path.join(self.LOG_DIR, log_filename)
      self.KEY_FILE = os.path.join(self.KEY_DIR, key_filename)".

Al encargarse Paramiko del login, este diccionario ya no lo podía usar y lo borré, por tanto: "self.Respuestas_Login = [
       "Permission denied, please try again.",
       "Access denied, try again.",
       "Login incorrect",
       "Authentication failed",
       "Password incorrect",
       "Invalid Login",
       "Wrong password",
    ]". 
Pero tenía que adaptar las partes donde lo usaba. 

Revisando el método procesar_login, que era central, indispensable para el honeypot en protocolo telnet, con los conn y conn.sendall(), me di cuenta que ya no era necesario. Se había quedado totalmente obsoleto. Ya no necesitaba administrar el login, ni los loggers asociados, ni los intentos, ni leer del socket, ni extraer credenciales, ni simular respuestas... Nada. 

Eso sí, el last login, que ya tenía en procesar_login y, por tanto, en telnet, quería tenerlo también en SSH y por eso lo incluí otra vez. Lo volví a escribir de cero para que apareciera al conectarse.
Al probarlo, con aleatoriedad de días, horas y minutos, con un intervalo para que el 80% se produjeran variaciones de 5 en 5 minutos y el 20% entre todos los minutos de una hora, funcionaba perfectamente. 

Ahora me interesaba que junto al last login apareciera una IP pública aleatoria. Para ello seguí un método parecido al del last login. 

Se me ocurrió también, para mayor realismo, hacer que igual que esa IP pública aleatoria se creaba, habilitar de forma dinámica comandos como "who", "w" o "last" para que apareciera tanto el disfraz que está en funcionamiento en la sesión en ese momento, como el resto de disfraces del diccionario con datos ficticios para que todo estuviera interrelacionado y diera gran realismo e interconexión entre todos los datos del honeypot. Para eso, decidí usar lambdas en respuestas falsas y cambiar en "procesar_shell" la paerte donde trataba comandos y enviaba respuestas falsas para hacerlo más flexible y que pudiera usar las 
lambdas dentro del método sin cambiar la lógica ni el lugar del diccionario de respuestas falsas.
Las lambdas las hice así: ""who": lambda estado: "\n".join(
        f"{s['user']:<8} {s['tty']:<10} {s['fecha']} ({s['ip']})"
        for s in estado["sesiones"] if s["activo"]
         ) + "\n",
    "w": lambda estado: "USER     TTY      FROM            LOGIN@   IDLE   JCPU   PCPU WHAT\n" + "\n".join(
        f"{s['user']:<8} {s['tty']:<8} {s['ip']:<15} {s['fecha']:<7}   0.00s  0.01s  0.00s -bash"
        for s in estado["sesiones"] if s["activo"]
    ) + "\n",
    "last": lambda estado: "\n".join(
        f"{s['user']:<8} {s['tty']:<10} {s['ip']:<15} {s['fecha']} "
        + ("still logged in" if s["activo"] else "")
        for s in estado["sesiones"]
        ) + "\n"".

Mientras que "procesar_shell" estaba así antes: "if comando_norm in RESPUESTAS:
         salida = RESPUESTAS[comando_norm]
         if isinstance(salida, str):
           salida = salida.format(
               HostName = estado.get("hostname"),
               sistema = estado.get("sistema")
           )
         if isinstance(salida, (list, tuple)):
            for linea in salida:
                self.enviar_bloque(chan, linea)
         else:
                self.enviar_bloque(chan, str(salida))".

Y ahora así: "if comando_norm in RESPUESTAS:
         salida = RESPUESTAS[comando_norm]
         
         if callable(salida):
             salida = salida(estado)
             
         if isinstance(salida, str):
             salida = salida.format(
                 HostName = estado.get("hostname"),
                 sistema = estado.get("sistema")
             )
             self.enviar_bloque(chan, salida)
             
         elif isinstance(salida, (list, tuple)):
             for linea in salida:
                 self.enviar_bloque(chan, linea)
         else:
             self.enviar_bloque(chan, str(salida))"

Y funcionó. Funcionaba muy bien. Al usar los comandos con lambdas, salían tres usuarios con sus IP y sus fechas aleatorias diferentes: root y dos de mis disfraces. Perfecto. 

Seguí después afinando cada vez más y más la lambdas hasta dejarlas así, buscando el máximo realismo que pudiera: 
""who": lambda estado: "\n".join(
        f"{s['user']:<8} pts/{i:<8} {s['fecha']} ({s['ip']})"
        for i, s in enumerate(estado["sesiones"])
        if s["activo"]
         ) + "\n",
    "w": lambda estado: ("USER     TTY      FROM            LOGIN@   IDLE   JCPU   PCPU WHAT\n" + "\n".join((lambda s: (
                f"{s['user']:<8} {s['tty']:<8} {s['ip']:<15} {s['fecha']:<7}  "
                f"{('0.00s' if (what := random.choice(['-bash','vim notas.txt','top','ssh server42','python3 script.py'])) in ('vim notas.txt','top') else random.choice(['0.00s','2:15','1:02:33'])):<6}  "
                f"0.01s  0.00s {what}"
            ) )(s) for s in estado["sesiones"] if s["activo"]
    ) + "\n"
         ),
    "last": lambda estado: "\n".join(
    f"{s['user']:<8} {s['tty']:<10} {s['ip']:<15} {s['fecha']} "
    + (
        "still logged in"
        if s["activo"]
        else (
            (lambda: "- crash")() if random.random() < 0.2 else
            (lambda: "- down")() if random.random() < 0.1 else
            (lambda: "- reboot")() if random.random() < 0.1 else
            (lambda minutos: f"- {(datetime.now() - timedelta(minutes=minutos)).strftime('%H:%M')}  ({minutos//60:02d}:{minutos%60:02d})"
            )(random.randint(1, 120))
        )
    )
    for s in estado["sesiones"]
     ) 
    + "\n"
    + ((lambda: (
            lambda inicio: 
                f"wtmp begins {inicio.strftime('%a %b %d %H:%M:%S %Y')}\n"
                f"btmp begins {inicio.strftime('%a %b %d %H:%M:%S %Y')}\n"
        )(
            min(
                datetime.strptime(s["fecha"], "%a %b %d %H:%M")
                for s in estado["sesiones"]
            ) - timedelta(days=random.randint(30,90))
        )
    )()
    )"
  
Añadí además otro comando más, el lado oscuro de "last": "lastb", que registra los intentos fallidos de inicio de sesión.
Me quedó así: 

"lastb": lambda estado: (
    "\n".join(
        f"{random.choice(['admin','test','oracle','postgres','guest']):<8} "
        f"pts/{i:<2}  {random.choice(['185.23.44.12','91.200.12.55','66.77.88.99']):<15} "
        f"{random.choice(['Mon Oct 20 12:15','Tue Oct 21 03:44','Wed Oct 22 18:01'])}"
        for i in range(random.randint(2,5))
    )
    + "\n\n"
    + f"btmp begins {(datetime.now() - timedelta(days=90)).strftime('%a %b %d %H:%M:%S %Y')}\n"
        )

Asimismo, aproveché para hacer dinámicos "ps aux" y "top" y que los procesos falsos fueran moviéndose y cambiando. 

También cambié otros comandos como "history" para que ofreciera respuesta realista. 

También eliminé otro método que para SSH ya no me hacía falta: "def extraer_credenciales(self, linea: str):      
     linea = (linea or "").strip().replace("\r", "")
     if not linea:
         return None, None
     if ":" in linea:
         u, p = linea.split(":", 1)
         return u.strip(), p.strip()
      
     partes = linea.split()
     if len(partes) == 2:
         return partes[0].strip(), partes[1].strip()
     
     return None, linea.strip()".

También tuve que adaptar el threading del método "iniciar" para que funcionara con Paramiko. Antes lo tenía así: " with ThreadPoolExecutor(max_workers=20) as executor:
          while True:
              try:
                conn, addr = s.accept()
                conn.settimeout(30)
                print(f"[DEBUG] Conexión aceptada de {addr}")
                executor.submit(self.manejar_conexion, conn, addr)
              except socket.timeout:
                  continue  ".

Pero Paramiko no funciona con conn, sino con chan y transport. Sin embargo, esa parte valía. Lo que tuve que hacer es añadir esta pequeña línea dentro de manejar_conexion, después de la obtención del canal de sesión, justo cuando se ha creado el estado, pero antes de entrar en el bucle del shell. Lo dejé en 1 minuto: "chan.settimeout(60)". Si en 1 minuto el atacante no hace nada y se detecta la inactividad, se cierra la conexión. 

Como último detalle de este proyecto, hices unos pequeños cambios que esperaba que me dieran un plus de realismo final: agrupar los comandos según lo que tardan en ofrecer resultados y usar una distribución gaussiana (random.gauss) para distrbuir sus tiempos.
De hecho, incluí más comandos de los que tenía mi diccionario por si algún día los añadía. Nunca se sabe si puedo volver a este proyecto y mejorarlo. 
Así que los dejé así: "cmds_ligeros = {"whoami","id","hostname","pwd","echo $SHELL","ls","ls -la","ls /var/www/html",
              "cat /etc/issue","cat /etc/passwd","cat /etc/shadow","uname -a","lsb_release -d",
              "who","w","last","lastb","nmap"}
cmds_medios = {"uptime","df -h","du -sh /var/www/html","free -h","lsblk","history",
               "cat /root/.ssh/id_rsa","netstat -tulnp","sudo -l"}
cmds_pesados = {"ps aux","top -b -n 1","mysql -u root","apt-get update","apt-get upgrade -y",
              "wget","scp","nano","vi"}".

Luego este pequeño método distribuía siguiendo una distribución gaussiana las latencias de los comandos agrupados por tipos: "def simulación_de_latencia(self, command):
     if command in self.cmds_ligeros:
        delay = max(0.05, random.gauss(0.3, 0.1))
     elif command in self.cmds_medios:
        delay = max(0.2, random.gauss(1.0, 0.3))
     elif command in self.cmds_pesados:
        delay = max(0.5, random.gauss(2.5, 0.7))
     else:
        delay = max(0.1, random.gauss(0.8, 0.3))
     time.sleep(delay)". 
Los convertí previamente en atributos de instancia en el init de la clase Honeypot y simplemente tuve ahora que usarlos con self. 
Al probar el honeypot tras eso, me topé con la agradable y curiosa sensación de experimentar cómo algunos comandos tardaban mucho y otros muy poco. Quedó verdaderamente bien. 
Además de eso, en procesar_shell hice cambios para hacer que el comando "history" ofreciera mi lista falsa, estática, y también los comandos a medida que se escribían en la shell, de manera que pareciera un history auténtico, que va acumulando comandos por orden. Además limité su longitud a 100 con: 

"if len(self.historial) > 100:
            self.historial = self.historial[-100:]"

El bloque entero quedaba así: "self.historial.append(comando_norm)
         if len(self.historial) > 100:
            self.historial = self.historial[-100:]

         if comando_norm == "history":
             salida = ""
             for i, cmd in enumerate (self.historial, start=1):
                salida += f"{i} {cmd}\n"
             self.enviar_bloque(chan, salida)
             return salida     ".

Este bloque lo puse antes de cuando se da la respuesta falsa para que no haya problemas de duplicaciones o de que no encuentre el comando (ya que lo he borrado del diccionario de respuestas falsas al hacerlo ahora dinámico).

En un entorno de pruebas reales, funcionó correctamente y pude recoger datos, con lo cual lo doy por terminado de modo exitoso.

Licencia

MIT


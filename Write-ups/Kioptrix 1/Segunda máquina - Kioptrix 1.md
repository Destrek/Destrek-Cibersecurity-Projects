
Esta es la segunda máquina que voy a hacer. Voy a intentar seguir en estos apuntes una estructura más definida y clara que en la anterior máquina. Aunque la máquina sólo contiene un único servicio vulnerable, voy a probar el flujo habitual y típico del pentesting: reconocimiento y enumeración, explotación, escalada de privilegios y post-explotación. 

El objetivo de esta máquina es claro: conseguir acceso root. 


Advertencia: por motivos de privacidad, todas las IP han sido modificadas en las capturas. Las no relevantes están censuradas y las de las VM cambiadas por IP falsas. Vamos a asumir que mi VM atacante es: 192.168.56.101 y Kioptrix (la máquina vulnerable): 192.168.56.102

## Reconocimiento y enumeración


1º:  buscamos la IP dentro de nuestra red. Para ello, usamos Netdiscover o Nmap. Yo he tenido problemas con mi propia red NAT, ya que no conseguía encontrar la IP de la máquina y, por tanto, acceder a ella. Por eso, tuve que cambiar las VM empleadas a Bridge y funcionó. 

Consejo: **Si no funciona con NAT, cambiad a Bridge.** 


Aunque probé ambas formas de encontrar la IP de la máquina, con la conseguí reconocerla y enumerar sus servicios después de los cambios que he mencionado fue con Nmap.

2º:  hice este escaneo:

![[1nmap.jpg]]

3º:  después de ver la IP, probé a enumerar sus servicios:

![[2nmap.jpg]]

Con esto comprobé que ésta, en efecto, era la máquina Kioptrix. La había detectado y tenía todos los servicios al descubierto que podía probar:

- **22/tcp – SSH (OpenSSH 2.9p2)** 
- **80/tcp – HTTP (Apache 1.3.20)** -
- **111/tcp – RPC (rpcbind)** 
- **139/tcp – Samba (smbd)** 
- **443/tcp – HTTPS (Apache con mod_ssl)** 
- **1024/tcp – RPC status**

Quedaba claro que la máquina estaba activa en red y lista para pasar a la siguiente fase: la de explotación. 

## Explotación


### A través de Samba


- Samba: puerto 139.
- Servicio: Samba smbd 2.2.x.
- Hallazgos: fácilmente explotable a través del exploit trans2open overflow (CVE‑2003‑0201).
- Impacto: crítico → compromete confidencialidad, integridad y disponibilidad al obtener root.
- Explotación práctica: Metasploit (exploit/linux/samba/trans2open)



Podemos probar varias vías para intentar conseguir el root. Pero vamos a probar primero a explotar Samba. Este servicio lo podemos explotar con "trans2open". Este exploit debería permitir aprovechar la vulnerabilidad del servicio y darnos una shell como root. 
Para buscarlo usamos searchsploit:

![[(3.jpg]]

En concreto, de todos estos, nos quedamos con: 

	"Samba 2.2.8 (Linux x86) - 'trans2open' Remote Overflow (Metasploit)
	| linux_x86/remote/16861.rb"

Este corresponde al sistema operativo de la máquina Kioptrix (es muy antiguo). 

Una vez hemos localizado el exploit que vamos a usar, abrimos msfsconsole. 

Cargamos el módulo en msfconsole:

![[4.jpg]

Configuramos los parámetros de Metasploit para usar el exploit:

![[5.jpg]]

Los puertos pueden dar problema, como me pasó a mí. Por ello, si os sucede, recomiendo usar otros puertos. Con el 5555 me funcionó.

![[(6.jpg]]

La shell estaba ya abierta. De hecho, había varias sesiones abiertas, pero con una es suficiente. Esto nos lleva al siguiente paso.

## Escalada de privilegios


A partir de aquí los privilegios están escalados, porque usando el exploit tenemos acceso root: 

![[7.jpg]]


Basta con hacer un whoami o un id para darnos cuenta de que, así, tenemos ya el acceso deseado.

## Post-Explotación

Estando en esta fase, lo que queda es explorar el sistema por dentro y ver qué encontramos. 
Podemos probar ls, ls -l, ls -la, cat /etc/passwd, cat /etc/shadow...

Al hacer cat /etc/shadow, por ejemplo, encontramos tres hashes que pueden crackearse con John The Ripper:

![[8.jpg]]


Esto es una pequeña muestra. Arriba del todo sale otro del propio usuario root. 

Recogemos los hashes: 

	"cat /etc/shadow > /tmp/shadow11.txt"

Y luego los pasamos a nuestra VM y los crackeamos. 

![[(9.jpg]]


La forma más sencilla para pasar las contraseñas desde la shell de Metasploit que encontré fue esta: con download.

Una vez tenemos los hashes los podemos intentar crackear. 

Los hashes extraídos usaban el algoritmo md5crypt con distintos salts. Esto implica que cada contraseña se calcula con un valor aleatorio único, dificultando ataques de rainbow tables y obligando a probar cada hash contra cada hash individualmente.


![[(10.jpg]]

John no consiguió crackear ninguno de los hashes. Pero éste no era el objetivo principal de la máquina, así que seguí adelante con otra cosa. 

Si buscamos con locate los directorios que tienen que ver con email, veremos muchos:

![[11.jpg]]

Entre todos los directorios que salen, hay uno que es interesante, y es:

			"/var/spool/mail/root"


¿Qué hay dentro? Un mensaje. 

![[12.jpg]]


Nos felicita por conseguir superar la máquina y nos avisa de que la del nivel 2 no será tan fácil. 

Con esto, por esta vía estaría terminada la máquina. 


### A través de HTTP


-  HTTP: puerto 80.
- Servicio: Apache httpd 1.3.20 Unix (Red-Hat/Linux) mod_ssl/2.8.4 OpenSSL/0.9.6b .
- Hallazgos: 
	- Explotable a través de los exploits OpenFuck, que explota mod_ssl (CVE‑2002‑0083)
	- Y ptrace-kmod, que es un exploit local (CVE‑2003‑0127).
- Impacto: crítico → OpenFuck te abre una shell que te permite entrar como usuario Apache y ptrace-kmod te permite escalar a root directamente.
- Explotación práctica: OpenFuck.c + ptrace-kmod.c


#### Explotación

En el reconocimiento de la máquina en el puerto 80 vemos que su versión es: "Apache httpd 1.3.20 ((Unix)  (Red-Hat/Linux) mod_ssl/2.8.4 OpenSSL/0.9.6b)". En mod_ssl es donde está la vulnerabilidad que nos permitirá entrar en el sistema y escalar privilegios. 

Con esto en cuenta, vamos a buscar vulnerabilidades para el servicio HTTP. Pero los módulos ya no contienen exploits en Metasploit para esta vulnerabilidad. Así que hay que descargarlo manualmente, instalar las dependencias y compilarlo. 

![[13.jpg]]


Las dependencias:

![[14.jpg]]


Y compilamos:

![[15.jpg]]


Con bastante paciencia, intentamos lanzar el exploit manualmente (y varias veces con varias combinaciones hasta que funcione una):


![[(16.jpg]]


Si todo va bien deberíamos tener una shell habilitada:

![[17.jpg]]


Al hacer whoami vemos que estamos en el usuario "apache".

![[18.jpg]]

Así que ya estamos dentro. Pero ahora toca pasar al siguiente punto.

#### Escalada de privilegios

Tenemos que conseguir acceso al usuario root.  Podemos usar el exploit ptrace-kmod para usarlo contra el kernel y ganar acceso root. Lo descargamos: 

![[19.jpg]]



¿Cómo lo pasamos de la VM atacante a Kioptrix? Pues levantando un sencillo servidor HTTP con Python para descargarlo desde dentro: 

![[20.jpg]]

Después desde la shell de Kioptrix hacemos la petición al servidor de la VM atacante:

![[21.jpg]]

Compilamos y ejecutamos:

![[22.jpg]]


Y comprobamos si todo ha funcionado: 

![[23.jpg]]


Ya somos root y podemos hacer exactamente lo mismo que antes en Samba: explorar, buscar archivos, contraseñas, directorios..., etc. 


Con esto queda claro que hay varias maneras de conseguir adentrarse en la máquina y escalar los privilegios. Lo que podemos aprender de esta máquina es que la fase de reconocimiento es bastante importante. Ser capaz de encontrar la IP de la máquina que vamos a atacar es imprescindible si queremos enumerar sus servicios e incluso atacarla. Por eso, usar las herramientas adecuadas y cerciorarse de que tienes la máquina localizada es algo esencial. 


Conclusiones:

• 	Fase de Reconocimiento
	• 	Enumeración de puertos: 139 (Samba), 443 (Apache/mod_ssl).
	
• 	Fase de Explotación (Vía 1 – Samba)
	• 	Uso de Trans2open → root inmediato.
	
• 	Fase de Explotación (Vía 2 – HTTP)
	• 	Uso de OpenFuck contra mod_ssl → shell como apache.
	• 	Transferencia y ejecución de p.trace-kmod.c → root.
	
• 	Fase de Escalada
	• 	Samba: no necesaria.
	• 	HTTP: necesaria, lograda con exploit local.
	
• 	Fase de Post‑explotación
	• 	Extracción de hashes, exploración de directorios , validación del mensaje final.




El contenido de este trabajo es para fines educativos en entornos controlados. El autor no se hace cargo de posibles usos indebidos o maliciosos que puedan hacerse de la información que contiene. 
El propósito de estos ejercicios es aprender cómo funcionan las vulnerabilidades y mejorar las defensas de los sistemas. 
Estas son máquinas diseñadas específicamente para ser vulneradas y exploradas.

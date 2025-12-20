import socket
from datetime import datetime, timedelta
import requests
import time
import csv
import os
import random
import time
import uuid
import hashlib
import mimetypes
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import paramiko
from paramiko import RSAKey

time.sleep(1)

# Configuración
HOST = "0.0.0.0"       # Escucha en todas las interfaces
PORT = 22            # Puerto honeypot
LOG_FILE = "honeypot.log"
ip_host = "192.168.2.130"
HostNames = {
            "CesarSN": "Ubuntu 20.04", 
             "MiguelRF": "Debian 11",
             "JuanMR": "CentOS 7",
             "RockyBalboaTL": "Kali Linux",
             "HugoED": "Arch Linux",
             "JohnMclaneGN": "Ubuntu 22.04"
             }

CREDENCIALES_ACEPTADAS = {
         "root": {"1234", "toor", "123456", "root", "12345", 
                  "password", "qwerty", "12345678", "letmein", "hunter2"},
         "admin": {"admin", "1234", "password", "123456",
                   "changeme", "welcome1"}
      }

HostName, sistema = random.choice(list(HostNames.items()))
Prompt = {"usuario": "admin",
          "hostname": HostName}

Banners = {"Ubuntu 20.04": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
           "Debian 11": "SSH-2.0-OpenSSH_8.4p1 Debian-5+deb11u1",
           "CentOS 7": "SSH-2.0-OpenSSH_7.4p1 RedHat-10",
           "Kali Linux": "SSH-2.0-OpenSSH_9.2p1 Debian-2",
           "Arch Linux": "SSH-2.0-OpenSSH_9.6p1",
           "Ubuntu 22.04": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.10"

}


# Diccionario de comandos trampa y respuestas falsas
RESPUESTAS = {
    "uname -a": "Linux {HostName} 5.10.0-23-amd64 #1 SMP {sistema} x86_64 GNU/Linux \n",
    "lsb_release -d": "Description:\t{sistema} \n",
    "hostname": "{HostName} \n",
    "cat /etc/issue": "{sistema} \\n \\l \n",
    "whoami": "root \n",
    "id": "uid=0(root) gid=0(root) groups=0(root) \n",
    "echo $SHELL": "/bin/bash \n",
    "uptime": " {HostName} up 12 days,  4:32,  1 user,  load average: 0.00, 0.01, 0.05 \n",

    # Navegación y ficheros
    "pwd": "/root\n",
    "ls": "drwxr-xr-x  2 root root 4096 Aug 30 09:12 bin\n"
          "drwxr-xr-x  3 root root 4096 Aug 30 09:12 boot\n"
          "drwxr-xr-x  5 root root 4096 Aug 30 09:12 dev\n"
          "drwxr-xr-x 77 root root 4096 Aug 30 09:12 etc\n"
          "drwx------  4 root root 4096 Aug 30 09:12 root\n"
          "drwxr-xr-x  6 root root 4096 Aug 30 09:12 home\n",
    "ls -la": "total 48\n"
              "drwx------  4 root root 4096 Aug 30 09:12 .\n"
              "drwxr-xr-x 20 root root 4096 Aug 30 09:12 ..\n"
              "-rw-------  1 root root  570 Aug 30 09:12 .bash_history\n"
              "-rw-r--r--  1 root root 3106 Aug 30 09:12 .bashrc\n"
              "drwx------  2 root root 4096 Aug 30 09:12 .ssh\n",
    "ls /var/www/html": "-rw-r--r-- 1 www-data www-data  2345 Aug 29 14:22 index.php\n"
                        "-rw-r--r-- 1 www-data www-data   543 Aug 29 14:22 config.php\n"
                        "-rw-r--r-- 1 www-data www-data   120 Aug 29 14:22 db.php\n",

    # Lectura de archivos
    "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\n"
                       "usuario:x:1000:1000::/home/usuario:/bin/bash\n"
                       "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n",
    "cat /etc/shadow": "cat: /etc/shadow: Permission denied\n",
    "cat /root/.ssh/id_rsa": "-----BEGIN RSA PRIVATE KEY-----\n"
                             "Proc-Type: 4,ENCRYPTED\n"
                             "DEK-Info: AES-128-CBC,AB12CD34EF56...\n"
                             "[REDACTED]\n"
                             "-----END RSA PRIVATE KEY-----\n",

    # Procesos y red
    "ps aux": lambda estado: (
    "USER          PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n" +
    "\n".join(
        [
            # Procesos de sistema
            f"{'root':<12}{1:>6}{0.0:>6.1f}{0.1:>6.1f}{1580:>8}{540:>7} {'?':<8}{'Ss':<3}{'Sep15':>7}{'0:01':>8} /sbin/init",
            f"{'root':<12}{303:>6}{0.0:>6.1f}{0.2:>6.1f}{2345:>8}{820:>7} {'?':<8}{'Ss':<3}{'Sep15':>7}{'0:00':>8} /usr/sbin/sshd",
            f"{'root':<12}{626:>6}{0.0:>6.1f}{0.1:>6.1f}{1980:>8}{600:>7} {'?':<8}{'S':<3}{'Sep15':>7}{'0:00':>8} /usr/sbin/cron",
            f"{'syslog':<12}{1092:>6}{0.0:>6.1f}{0.1:>6.1f}{2100:>8}{700:>7} {'?':<8}{'S':<3}{'Sep15':>7}{'0:00':>8} /usr/sbin/rsyslogd",
            f"{'message+':<12}{1388:>6}{0.0:>6.1f}{0.1:>6.1f}{2500:>8}{800:>7} {'?':<8}{'S':<3}{'Sep15':>7}{'0:00':>8} /usr/bin/dbus-daemon --system",
            f"{'root':<12}{1617:>6}{0.0:>6.1f}{0.2:>6.1f}{2600:>8}{900:>7} {'?':<8}{'S':<3}{'Sep15':>7}{'0:00':>8} /lib/systemd/systemd-journald",
            f"{'root':<12}{1753:>6}{0.0:>6.1f}{0.2:>6.1f}{2700:>8}{950:>7} {'?':<8}{'Sl':<3}{'Sep15':>7}{'0:00':>8} /usr/lib/policykit-1/polkitd --no-debug",
            f"{'root':<12}{1892:>6}{0.0:>6.1f}{0.3:>6.1f}{2800:>8}{1000:>7} {'?':<8}{'Sl':<3}{'Sep15':>7}{'0:00':>8} /usr/sbin/NetworkManager --no-daemon",
            f"{'root':<12}{1902:>6}{0.0:>6.1f}{0.2:>6.1f}{2600:>8}{850:>7} {'?':<8}{'S':<3}{'Sep15':>7}{'0:00':>8} /lib/systemd/systemd-logind",
            f"{'www-data':<12}{2000:>6}{0.0:>6.1f}{0.3:>6.1f}{3456:>8}{1200:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} /usr/sbin/apache2 -k start",
            f"{'mysql':<12}{2393:>6}{2.4:>6.1f}{1.2:>6.1f}{45000:>8}{6200:>7} {'?':<8}{'Sl':<3}{'Oct29':>7}{'0:05':>8} /usr/sbin/mysqld",
            f"{'postfix':<12}{2539:>6}{0.0:>6.1f}{0.1:>6.1f}{3100:>8}{900:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} qmgr -l -t unix -u",
            f"{'daemon':<12}{2924:>6}{0.0:>6.1f}{0.0:>6.1f}{1500:>8}{400:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} /usr/sbin/atd",
            f"{'nobody':<12}{3526:>6}{0.0:>6.1f}{0.0:>6.1f}{1200:>8}{300:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} /usr/sbin/dnsmasq",
            # Procesos del kernel
            f"{'root':<12}{4058:>6}{0.0:>6.1f}{0.0:>6.1f}{0:>8}{0:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} [kworker/0:1]",
            f"{'root':<12}{4339:>6}{0.0:>6.1f}{0.0:>6.1f}{0:>8}{0:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} [migration/1]",
            f"{'root':<12}{4618:>6}{0.0:>6.1f}{0.0:>6.1f}{0:>8}{0:>7} {'?':<8}{'S':<3}{'Oct29':>7}{'0:00':>8} [rcu_sched]",
            # Sesiones de usuarios
            f"{'root':<12}{6339:>6}{1.2:>6.1f}{1.1:>6.1f}{5838:>8}{4726:>7} {'pts/0':<8}{'S':<3}{'Oct29':>7}{'0:04':>8} -bash",
            f"{'user':<12}{6418:>6}{0.8:>6.1f}{0.7:>6.1f}{7410:>8}{2058:>7} {'pts/1':<8}{'R':<3}{'Oct29':>7}{'0:03':>8} -bash",
            f"{'user':<12}{6522:>6}{0.5:>6.1f}{0.6:>6.1f}{8120:>8}{2300:>7} {'pts/2':<8}{'S':<3}{'Oct29':>7}{'0:02':>8} vim notes.txt",
            f"{'user':<12}{7259:>6}{1.5:>6.1f}{0.4:>6.1f}{9000:>8}{2500:>7} {'pts/3':<8}{'R':<3}{'Oct29':>7}{'0:01':>8} python3 script.py",
        ]
        +
        [   f"{s['user']:<12}{random.randint(5000,7000):>6}{random.uniform(0.1,2.5):>6.1f}{random.uniform(0.1,1.5):>6.1f}"
            f"{random.randint(4000,9000):>8}{random.randint(1000,5000):>7} pts/{i:<3}{random.choice(['S','R','Sl']):<3}"
            f"{'Oct29':>7}{f'0:0{random.randint(0,5)}':>8} -bash"
            for i, s in enumerate([u for u in estado["sesiones"] if u["activo"]], start=0)
        ]
        +
        # Procesos extra de ruido
        [
            f"{'user':<12}{random.randint(7001,7500):>6}{random.uniform(0.5,2.0):>6.1f}{random.uniform(0.3,1.0):>6.1f}"
            f"{9000:>8}{2500:>7} pts/{len([u for u in estado['sesiones'] if u['activo']])+1:<3}{'R':<3}"
            f"{'Oct29':>7}{'0:01':>8} python3 script.py",
            f"{'user':<12}{random.randint(7501,7600):>6}{0.0:>6.1f}{0.2:>6.1f}{7000:>8}{1500:>7} pts/{len([u for u in estado['sesiones'] if u['activo']])+2:<3}{'S':<3}"
            f"{'Oct29':>7}{'0:00':>8} vim notes.txt"])),
    "netstat -tulnp": "tcp        0      0 0.0.0.0:22       0.0.0.0:*     LISTEN      123/sshd\n"
                      "tcp        0      0 0.0.0.0:80       0.0.0.0:*     LISTEN      789/apache2\n"
                      "tcp        0      0 127.0.0.1:3306   0.0.0.0:*     LISTEN      456/mysqld\n",

    # Sistema de archivos y uso
    "df -h": "Filesystem      Size  Used Avail Use% Mounted on\n"
             "/dev/sda1        50G   45G  5G   90% /\n"
             "tmpfs           798M     0 798M    0% /dev/shm\n",
    "du -sh /var/www/html": "12M\t/var/www/html\n",

    # Historial y comandos
    
    "sudo -l": "Matching Defaults entries for root on {sistema}:\n"
               "    env_reset, mail_badpass,\n"
               "    secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n\n"
               "User root may run the following commands on this host:\n"
               "    (ALL) NOPASSWD: ALL\n",

    # Servicios y bases de datos
    "mysql -u root": "Welcome to the MySQL monitor.  Commands end with ; or \\g.\n"
                     "Your MySQL connection id is 12\n"
                     "Server version: 5.7.34-0ubuntu0.18.04.1 (Ubuntu)\n"
                     "Type 'help;' or '\\h' for help. Type '\\c' to clear the current input statement.\n",

    # Otros comandos típicos
    "who": lambda estado: "\n".join(
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
    + ((lambda inicio:
        f"wtmp begins {inicio.strftime('%a %b %d %H:%M:%S %Y')}\n"
        f"btmp begins {inicio.strftime('%a %b %d %H:%M:%S %Y')}\n"
    )(
        min(
            datetime.strptime(s["fecha"] + f" {datetime.now().year}", "%a %b %d %H:%M %Y")
            for s in estado["sesiones"]
        ) - timedelta(days=random.randint(30,90))
    )),
    "lastb": lambda estado: 
        ("\n".join(
        f"{random.choice(['admin','test','oracle','postgres','guest']):<8} "
        f"pts/{i:<2}  {random.choice(['185.23.44.12','91.200.12.55','66.77.88.99']):<15} "
        f"{(datetime.now() - timedelta(days=random.randint(1,120), hours=random.randint(0,23))).strftime('%a %b %d %H:%M')}"
        for i in range(random.randint(3,6))
    )
    + "\n\n"
    + f"btmp begins {(datetime.now() - timedelta(days=180)).strftime('%a %b %d %H:%M:%S %Y')}\n"),
    "top": lambda estado: (
    f"top - {time.strftime('%H:%M:%S')} up {random.randint(40,60)} days,  "
    f"{random.randint(0,23)}:{random.randint(0,59):02d},  "
    f"{len([u for u in estado['sesiones'] if u['activo']])+4} users,  "
    f"load average: {random.uniform(0.20,0.80):.2f}, {random.uniform(0.20,0.80):.2f}, {random.uniform(0.20,0.80):.2f}\n"
    f"Tasks: {random.randint(140,180)} total,   1 running, {random.randint(130,170)} sleeping,   0 stopped,   0 zombie\n"
    f"%Cpu(s): {random.uniform(2.0,6.0):4.1f} us,  {random.uniform(0.2,1.0):4.1f} sy,  0.0 ni, {random.uniform(90.0,97.0):4.1f} id,  "
    f"{random.uniform(0.1,0.5):4.1f} wa,  0.0 hi,  0.1 si,  0.0 st\n"
    f"KiB Mem :  4048576 total,  {random.randint(900000,1200000)} free,  {random.randint(1400000,1700000)} used,  {random.randint(1200000,1600000)} buff/cache\n"
    f"KiB Swap:  2097148 total,  2097148 free,        0 used.  {random.randint(2000000,2200000)} avail Mem\n\n"
    "  PID USER          PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND\n" +
    "\n".join([
        f"{2393:5d} mysql         20   0  45000   6200   900 S   {random.uniform(1.5,3.0):4.1f}  1.2   0:0{random.randint(5,9)}.3 mysqld",
        f"{7185:5d} user          20   0   9000   2500   500 R   {random.uniform(1.0,2.5):4.1f}  0.3   0:0{random.randint(1,3)}.1 python3",
        f"{6339:5d} root          20   0   5838   4726   800 S   {random.uniform(0.5,1.5):4.1f}  1.1   0:0{random.randint(4,6)}.4 bash",
        f"{6418:5d} JohnMclaneGN  20   0   7410   2058   600 R   {random.uniform(0.3,1.0):4.1f}  0.7   0:0{random.randint(2,4)}.2 bash",
        f"{6522:5d} RockyBalboaTL 20   0   8120   2300   700 S   {random.uniform(0.2,0.8):4.1f}  0.6   0:0{random.randint(1,3)}.0 vim",
        f"{7259:5d} HugoED        20   0   9000   2500   500 R   {random.uniform(1.0,2.0):4.1f}  0.4   0:0{random.randint(1,3)}.1 python3",
        f"{2000:5d} www-data      20   0   3456   1200   400 S   {random.uniform(0.1,0.5):4.1f}  0.3   0:0{random.randint(0,1)}.5 apache2",
        f"{ 303:5d} root          20   0   2345    820   300 S   {random.uniform(0.0,0.2):4.1f}  0.2   0:0{random.randint(0,1)}.2 sshd",
        f"{1388:5d} message+      20   0   2500    800   200 S   {random.uniform(0.0,0.2):4.1f}  0.1   0:0{random.randint(0,1)}.1 dbus-daemon",
        f"{1617:5d} root          20   0   2600    900   300 S   {random.uniform(0.0,0.2):4.1f}  0.2   0:0{random.randint(0,1)}.3 systemd-journal",
        f"{1753:5d} root          20   0   2700    950   350 S   {random.uniform(0.0,0.2):4.1f}  0.2   0:0{random.randint(0,1)}.2 polkitd",
    ])),
    "lsblk": "NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT\n"
             "sda      8:0    0   50G  0 disk \n"
             "└─sda1   8:1    0   50G  0 part /\n",
    "free -h": "              total        used        free      shared  buff/cache   available\n"
               "Mem:           1.6G        256M        512M        8.0M        828M        1.3G\n"
               "Swap:          2.0G          0B        2.0G\n",

    "nmap": "bash: nmap: command not found\r\n"
}

cmds_ligeros = {"whoami","id","hostname","pwd","echo $SHELL","ls","ls -la","ls /var/www/html",
              "cat /etc/issue","cat /etc/passwd","cat /etc/shadow","uname -a","lsb_release -d",
              "who","w","last","lastb","nmap"}
cmds_medios = {"uptime","df -h","du -sh /var/www/html","free -h","lsblk","history",
               "cat /root/.ssh/id_rsa","netstat -tulnp","sudo -l"}
cmds_pesados = {"ps aux","top -b -n 1","mysql -u root","apt-get update","apt-get upgrade -y",
              "wget","scp","nano","vi"}


class ServidorHoneypotSSH(paramiko.ServerInterface):
    
    def __init__(self, logger, estado_inicial = None):
        self.logger = logger
        self.estado = estado_inicial or {}
        self.pty_requested = False
        self.pty = {"term": None, "width": 80, "height": 24, "pixelwidth": 0, "pixelheight": 0, "modes": None }
        self.event = threading.Event()
        
    def get_allowed_auths(self, username):    
        return "password"    
    
    def check_auth_password(self, username, password):
        
        self.logger.crear_evento({
            "evento": "login_try",
            "usuario": None,
            "password": None,
            "usuario_intentado": username,
            "password_intentada": password,
            "session_id": self.estado.get("session_id"),
            "ip": self.estado.get("ip_remota"),
            "timestamp": datetime.now().isoformat()
        })
        if username in CREDENCIALES_ACEPTADAS and password in CREDENCIALES_ACEPTADAS[username]:
        
            self.estado["usuario"] = username
            self.estado["password"] = password
        
            self.logger.crear_evento({
                "evento": "login_success",
                "usuario": username,
                "password": password,
                "usuario_intentado": username,
                "password_intentada": password,
                "session_id": self.estado.get("session_id"),
                "ip": self.estado.get("ip_remota"),
                "timestamp": datetime.now().isoformat()
            })
            return 0
        
        else: 
            self.logger.crear_evento({
                "evento": "login_failed",
                "usuario_intentado": username,
                "password_intentada": password,
                "session_id": self.estado.get("session_id"),
                "ip": self.estado.get("ip_remota"),
                "timestamp": datetime.now().isoformat()
            })
            return 1

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return 0
        return 1
    
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        self.pty_requested = True
        self.pty.update({
             "term": term, "width": width, "height": height,
            "pixelwidth": pixelwidth, "pixelheight": pixelheight, "modes": modes
        })
        return True
    
class Honeypot:
 
 """
    Esta clase va a contener la estructura principal del honeypot.

 """

 def enviar_linea(self, chan, text=""):
    # Enviar una línea completa con CRLF
    chan.send((text.replace("\n", "\r\n") + "\r\n").encode())

 def enviar_bloque(self, chan, text):
    # Enviar un bloque de texto normalizado, sin prompt
    chan.send(text.replace("\n", "\r\n").encode())

 def enviar_prompt(self, chan, prompt):
    # Volver al inicio, limpiar la línea y pintar prompt
    chan.send(("\r\x1b[K" + prompt + " ").encode())
 
 def __init__(self, host, port, logger, key_filename="host_rsa.key"):
    self.host = host
    self.port = port
    self.logger = logger
    self.conexiones_activas = 0
    self.lock_conexiones = threading.Lock()
    self.intentos_por_ip = {}
    self.KEY_DIR = "keys"
    os.makedirs(self.KEY_DIR, exist_ok=True)
    self.KEY_FILE = os.path.join(self.KEY_DIR, key_filename)
    self.host_key = self.cargar_o_generar_clave()
    self.cmds_ligeros = cmds_ligeros
    self.cmds_medios = cmds_medios
    self.cmds_pesados = cmds_pesados
    self.historial = [
                "uname -a",
                "ls -la /etc/ssh",
                "vi /etc/ssh/sshd_config",
                "systemctl restart ssh",
                "tail -n 50 /var/log/auth.log",
                "grep Failed password /var/log/auth.log",
                "df -h",
                "free -m",
                "top -b -n 1",
                "apt-get update",
                "apt-get upgrade -y",
                "wget http://mirror.updates.net/patch_ssh.sh",
                "chmod +x patch_ssh.sh",
                "./patch_ssh.sh",
                "useradd tempadmin",
                "passwd tempadmin",
                "id tempadmin",
                "scp backup.tar.gz admin@192.168.1.45:/tmp/",
                "ping -c 2 intranet.local",
                "nano /etc/hosts",
                "cat /etc/passwd | tail -n 5",
                "rm -f patch_ssh.sh",
                "history",    
    ]
    
    os.makedirs("payloads", exist_ok=True) # Crea la carpeta "Payloads" al principio para usarla siempre que funcione y guardar en ella lo recogido.
    
    self.disfraces = {
            "CesarSN": {"os": "Ubuntu 20.04"}, 
             "MiguelRF":{"os": "Debian 11"},
             "JuanMR": {"os": "CentOS 7"},
             "RockyBalboaTL":{"os": "Kali Linux"},
             "HugoED": {"os": "Arch Linux"},
             "JohnMclaneGN": {"os":"Ubuntu 22.04"}
             }
    
    self.MOTDS: dict[str, list[str]] = {
"Ubuntu 20.04": ["""Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.4.0.91-generic x86_64)
    
 * Documentation: https://help.ubuntu.com 
 * Management: https://ubuntu.com/advantage
    
System information as of: Tue Sep 30 19:00:00 CEST 2025
0 updates can be applied immediately.  
  
The programs included with Ubuntu system are free software; ... 
Ubuntu comes with ABSOLUTELY NO WARRANTY.

"""],

"Debian 11": ["""Debian GNU/Linux 11 (bullseye)
     
The programs included with Debian GNU/Linux system are free software; 
the exact distribution terms for each program are described in 
/usr/share/doc/*/copyright. 
GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.

"""],

"CentOS 7": ["""CentOS 7 (Core) Kernel \\r on an \\m  Welcome to CentOS Linux 7 (Core) !

* Documentation: https://www.centos.org/docs/
* Support: https://wiki.centos.org  
* Forums: https://forums.centos.org/

"""],

"Kali Linux": ["""Kali GNU/Linux Rolling 
     
     The programs included with Kali GNU/Linux system are free software; 
     the exact distribution terms for each program are described in the
     individual files in /usr/share/doc/*/copyright. 
     
     Kali GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
     permitted by applicable law.
     
     """],
     
"Arch Linux": ["""Arch Linux \\r (\\l)
    
The programs included with the Arch Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Arch Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.

"""],

"Ubuntu 22.04": ["""Welcome to Ubuntu 22.04.4 LTS (GNU/Linux 5.15.0-112-generic x86_64)
    
* Documentation: https://help.ubuntu.com
* Management: https://ubuntu.com/advantage

System information as of: Tue Sep 30 19:00:00 CEST 2025
0 updates can be applied immediately.  
The programs included with Ubuntu system are free software; ...
Ubuntu comes with ABSOLUTELY NO WARRANTY.

"""]  

}      

    alias, perfil = random.choice(list(self.disfraces.items()))
    self.hostname = alias
    self.sistema = perfil["os"]
 
 def simulacion_de_latencia(self, command):
     if command in self.cmds_ligeros:
        delay = max(0.05, random.gauss(0.3, 0.1))
     elif command in self.cmds_medios:
        delay = max(0.2, random.gauss(1.0, 0.3))
     elif command in self.cmds_pesados:
        delay = max(0.5, random.gauss(2.5, 0.7))
     else:
        delay = max(0.1, random.gauss(0.8, 0.3))
     time.sleep(delay)
 
 def cargar_o_generar_clave(self) -> RSAKey:
     if os.path.exists(self.KEY_FILE):
         print(f"[DEBUG] Cargando clave de host desde {self.KEY_FILE}")
         return RSAKey(filename=self.KEY_FILE)
     else:
         print(f"[DEBUG] No existe ninguna clave de host. Generando una nueva en {self.KEY_FILE}")
         key = RSAKey.generate(2048)
         key.write_private_key_file(self.KEY_FILE)
         return key
        
    
 def generar_identificacion(self):
     return str(uuid.uuid4())
 
 def capturar_payload(self, estado, contenido:bytes, nombre_sugerido="payloads"):
     
     sha256 = hashlib.sha256(contenido).hexdigest()
     tamano = len(contenido)
     tipo_sugerido, _ = mimetypes.guess_type(nombre_sugerido)
     if not tipo_sugerido:
         tipo_sugerido = "application/octet-stream"
     
     texto = ""     
     try:
         texto = contenido.decode("utf-8")
         es_texto = True
     except UnicodeDecodeError:
         es_texto = False
         
     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
     base_nombre = f"{estado.get('session_id') or ''}_{timestamp}_{nombre_sugerido}"
     
     if es_texto:
           nombre_archivo = f"{base_nombre}.txt"
           ruta = os.path.join("payloads", nombre_archivo)
           with open(ruta, "w", encoding="utf-8") as f:
             f.write(texto)
             
           self.logger.crear_evento({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
             "ip": estado["ip_remota"] if "ip_remota" in estado else None,
             "port": estado["port"] if "port" in estado else None,
             "evento": "payload_script",
             "usuario": estado.get("usuario") or None,
             "comando": estado.get("ultimo_comando") or None,
             "archivo": nombre_archivo,
             "hash": sha256,
             "tamano": tamano,
             "tipo_payload": "script",
             "session_id": estado["session_id"] if "session_id" in estado else None,  
     })    
     else:
         nombre_archivo = base_nombre
         
         self.logger.crear_evento({
              "timestamp": datetime.now().isoformat(timespec="seconds"),
               "ip": estado["ip_remota"] if "ip_remota" in estado else None,
               "port": estado["port"] if "port" in estado else None,
               "evento": "payload_binario",
               "usuario": estado.get("usuario") or None,
               "comando": estado.get("ultimo_comando") or None,
                "archivo": nombre_archivo,
                "hash": sha256,
                "tamano": tamano,
                "tipo_payload": "binario",
                "session_id": estado["session_id"] if "session_id" in estado else None   
         })  
        
                                
 def geolocalizar(self, ip):
    """Obtiene ubicación aproximada de una IP usando ip-api.com"""
    try:
      r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
      data = r.json()
      if data.get("status") == "success":
         return {"pais": data.get("country") or None,
                "region": data.get("regionName") or None, 
                "ciudad": data.get("city") or None, 
                "isp": data.get("isp") or None, 
                "asn": data.get("as") or None
                }
      else:
         return {"pais": None, "region": None, "ciudad": None, "isp": None, "asn": None}
    except Exception as e:
       print(f"Error geolocalizando {ip}:{e}")
       return{"pais": None, "region": None, "ciudad": None, "isp": None, "asn": None}
    
 def iniciar(self):
    print("[DEBUG] Entrando en iniciar()")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   
     s.bind((self.host, self.port))
     s.listen()
     s.settimeout(10)
     print(f"Honeypot escuchando en {self.host}:{self.port}...")
     with ThreadPoolExecutor(max_workers=20) as executor:
          while True:
              try:
                conn, addr = s.accept()
                conn.settimeout(30)
                print(f"[DEBUG] Conexión aceptada de {addr}")
                executor.submit(self.manejar_conexion, conn, addr)
              except socket.timeout:
                  continue  

 def manejar_conexion (self, conn, addr):
      alias, perfil = random.choice(list(self.disfraces.items()))
      with self.lock_conexiones:
          self.conexiones_activas +=1
          activas = self.conexiones_activas
      ip = addr[0]
      try:
            reverse_dns = socket.gethostbyaddr(ip)[0]
      except Exception:
            reverse_dns = None 
               
      estado = {
                "session_id": self.generar_identificacion(),
                "start_time": datetime.now().isoformat(),
                "ip_remota": ip,
                "sistema": perfil["os"],
                "hostname": alias,
                "prompt_root": f"root@{alias}:~#",
                "prompt_admin": f"admin@{alias}:~$",
                "banner": Banners[perfil["os"]],
                "motd": self.MOTDS.get(perfil["os"], []),
                "geo": self.geolocalizar(ip),
                "reverse_dns": reverse_dns,
                "usuario": None,
                "intentos": 0,
                "aceptado": False,
                "historial": [],
                "usuario_asignado": perfil.get("usuario_asignado", None),
                "usuario_intentado": None,
                "password_intentada": None}   
          
      self.logger.crear_evento({
          "evento": "nueva_conexion",
          "ip": addr[0],
          "port": addr[1],
          "conexiones_activas": activas,
          "thread": threading.current_thread().name,
          "session_id": estado["session_id"],
          "hostname_simulado": estado["hostname"],
          "sistema_simulado": estado["sistema"],
          "usuario_asignado": estado["usuario_asignado"],
          "usuario_intentado": None,
          "password_intentada": None,
          "pais": estado["geo"].get("pais") if estado.get("geo") else None,
          "region": estado["geo"].get("region") if estado.get("geo") else None,
          "ciudad": estado["geo"].get("ciudad") if estado.get("geo") else None,
          "isp": estado["geo"].get("isp") if estado.get("geo") else None,
          "asn": estado["geo"].get("asn") if estado.get("geo") else None,
      })   
      print(f"[DEBUG] Entrando en manejar_conexion con {addr}")
            
      print(f"[Honeypot] Nueva sesión establecida {estado['session_id']} con disfraz:"
            f"{estado['hostname']} ({estado['sistema']})")
      
      transport = paramiko.Transport(conn)
      transport.add_server_key(self.host_key)
      transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3"
      
      server = ServidorHoneypotSSH(self.logger, estado_inicial = estado)
      
      try:
          transport.start_server(server=server)
      except Exception as e:
          self.logger.crear_evento({
            "evento": "handshake_error",
            "detalle": str(e),
            "session_id": estado["session_id"],
            "timestamp": datetime.now().isoformat()
        })
          transport.close()
          conn.close()
          return
    
      chan = transport.accept(timeout=15)
      if chan is None:
            transport.close()
            conn.close()
            return
        
      chan.settimeout(60)
        
      self.logger.crear_evento({
            "evento": "banner_enviado",
            "session_id": estado["session_id"],
            "timestamp": datetime.now().isoformat()
        })

      try:
          self.bucle_de_shell(chan, estado)
      finally:
          with self.lock_conexiones:
              self.conexiones_activas -= 1
              activas = self.conexiones_activas
          inicio = datetime.fromisoformat(estado["start_time"])
          duracion = (datetime.now() - inicio).total_seconds()
          time.sleep(random.uniform(0.2, 0.5))
          self.logger.crear_evento({
              "evento": "conexion_cerrada",
              "ip": addr[0],
              "port": addr[1],
              "conexiones_activas": activas,
              "thread": threading.current_thread().name,
              "session_id": estado.get("session_id"),
              "hostname_simulado": estado.get("hostname"),
              "sistema_simulado": estado.get("sistema"),
              "reverse_dns": estado.get("reverse_dns"),
              "pais": estado["geo"].get("pais") if estado.get("geo") else None,
              "region": estado["geo"].get("region") if estado.get("geo") else None,
              "ciudad": estado["geo"].get("ciudad") if estado.get("geo") else None,
              "isp": estado["geo"].get("isp") if estado.get("geo") else None,
              "asn": estado["geo"].get("asn") if estado.get("geo") else None,
              "duracion": duracion,
              "usuario_asignado": estado["usuario_asignado"],
              "usuario_intentado": None,
              "password_intentada": None
          })
          print(f"[DEBUG] Conexión cerrada con {addr}")
          chan.close()
          transport.close()
          conn.close()                                 
      
 def credencial_aceptada(self, user: str, pwd:str) -> bool:
      user = user.strip().lower()
      pwd = pwd.strip()
      return user in CREDENCIALES_ACEPTADAS and pwd in CREDENCIALES_ACEPTADAS[user]


 def bucle_de_shell(self, chan, estado):
    """
    Motor de la sesión SSH: gestiona el bucle de lectura/escritura
    y delega la lógica de comandos a procesar_shell. Admite backspace, Ctrl+C y Ctrl+D.
    """
    days_ago = random.randint(3, 30)
    hour = random.randint(8, 23)
    if random.random() < 0.8:
        minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    else:
        minute = random.randint(0, 59)      
    last_time = datetime.now() - timedelta(days=days_ago)
    last_time = last_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    prefijos_direccionip = [185, 91, 62, 66, 104, 202, 218, 223]
    while True:
        octetos = [
            random.choice(prefijos_direccionip),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(1, 254)
        ]
        ip_fake = ".".join(map(str, octetos))
        
        if not(ip_fake.startswith("100") or
               ip_fake.startswith("192.0.2.") or
               ip_fake.startswith("198.51.100.") or
               ip_fake.startswith("203.0.113.")):
            break
    last_login = f"Last login: {last_time.strftime('%a %b %d %H:%M:%S %Y')} from {ip_fake}\r\n"
    chan.send(last_login.encode())
    chan.send(b"\r\n")
    
    estado["last_ip"] = ip_fake
    estado["last_fecha"] = last_time.strftime("%a %b %d %H:%M")
    
    estado["sesiones"] = []
    
    estado["sesiones"].append({
        "user": "root",
        "tty": "pts/0",
        "ip": estado["last_ip"],
        "fecha": estado["last_fecha"],
        "activo": True
    })
    
    usuarios = list(HostNames.keys())
    for _ in range(random.randint(2, 4)):
        estado["sesiones"].append({
            "user": random.choice(usuarios),
            "tty": f"pts/{random.randint(1, 3)}",
            "ip":  ".".join(map(str, [
                    random.choice([185, 91, 62, 66, 104, 202, 218, 223]),
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(1, 254)
                ])),
            "fecha": (datetime.now() - timedelta(days=random.randint(1, 10))).strftime("%a %b %d %H:%M"),
            "activo": random.choice([True, False])
        })
    
    for linea in estado.get("motd", []):
        chan.send(linea.replace("\n", "\r\n").encode())
        
    prompt = estado["prompt_root"] if estado.get("usuario") == "root" else estado["prompt_admin"]   
    self.enviar_prompt(chan, prompt)
    
    linea = []
    pty = estado.get("pty", False)
    
    while True:
        try:
            data = chan.recv(1024)
            if not data:
                break
            for byte in data:
                ch = chr(byte)
                
                if ch in ('\r', '\n'):
                 chan.send(b"\r\n")
                 comando = "".join(linea).strip()
                 linea.clear()
                 
                 if comando:
                     resultado = self.procesar_shell(chan, comando, estado)
                     if resultado == "cerrar":
                         return
                     if resultado:
                         self.enviar_bloque(chan, resultado)
                     
                 prompt = estado["prompt_root"] if estado.get("usuario") == "root" else estado["prompt_admin"]
                 self.enviar_prompt(chan, prompt)
                 continue
                
                if ch in ('\x7f', '\b'):
                    if linea:
                        linea.pop()
                        if not pty:
                         chan.send(b"\b \b")
                    continue
                
                if ch == '\x03':
                    linea.clear()
                    self.enviar_linea(chan, "^C")
                    self.enviar_prompt(chan, prompt)
                    continue

                if ch == '\x04':
                    if not linea:
                        self.enviar_linea(chan)
                        self.enviar_linea(chan, "logout")
                        return        
                    continue
                
                linea.append(ch)
                if not pty:
                    if random.random() < 0.01:
                        chan.send((ch*2).encode())
                    else:
                        chan.send(ch.encode())
                            
        except socket.timeout:
            self.enviar_linea(chan, "\r\nSession timed out due to inactivity")
            self.logger.crear_evento({
                "evento": "timeout_inactividad",
                "session_id": estado["session_id"],
                "timestamp": datetime.now().isoformat()
            })
            return
              
        except Exception as e:
            self.logger.crear_evento({
                "evento": "shell_error",
                "detalle": str(e),
                "session_id": estado["session_id"],
                "timestamp": datetime.now().isoformat()
            })
            break
 
 
 def procesar_shell(self, chan, comando, estado):
      comando_norm = " ".join((comando or "").split())
      estado.setdefault("historial", []).append(comando_norm)
    
      self.logger.crear_evento({
       "session_id": estado["session_id"],   
       "evento": "cmd_exec",
       "usuario": estado.get("usuario"),
       "ip": estado["ip_remota"],
       "comando": comando_norm,
       "timestamp": datetime.now().isoformat(),
       "hostname_simulado": estado["hostname"],
        "sistema_simulado": estado["sistema"],
        "reverse_dns": estado.get("reverse_dns"),
        "pais": estado["geo"].get("pais") if estado.get("geo") else None,
        "region": estado["geo"].get("region") if estado.get("geo") else None,
        "ciudad": estado["geo"].get("ciudad") if estado.get("geo") else None,
        "isp": estado["geo"].get("isp") if estado.get("geo") else None,
        "asn": estado["geo"].get("asn") if estado.get("geo") else None,
        "usuario_asignado": estado["usuario_asignado"],
        "usuario_intentado": estado.get("usuario_intentado"),
        "password_intentada": estado.get("password_intentada")
    })
      time.sleep(random.uniform(0.1, 0.4))
      
      if comando_norm in("exit", "logout"):
       chan.send(b"logout\nConnection closed.\n")
       resumen = {
       "session_id": estado["session_id"],    
       "evento": "sumario_sesion",
       "usuario": estado.get("usuario"),
       "ip": estado.get("ip_remota"),
       "timestamp": datetime.now().isoformat(),
       "duracion": (datetime.now() - estado.get("ts_inicio", datetime.now())).total_seconds(),
       "comando": " ; ".join(estado.get("historial", [])),
       "hostname_simulado": estado["hostname"],
        "sistema_simulado": estado["sistema"],
        "reverse_dns": estado.get("reverse_dns"),
        "pais": estado["geo"].get("pais") if estado.get("geo") else None,
        "region": estado["geo"].get("region") if estado.get("geo") else None,
        "ciudad": estado["geo"].get("ciudad") if estado.get("geo") else None,
        "isp": estado["geo"].get("isp") if estado.get("geo") else None,
        "asn": estado["geo"].get("asn") if estado.get("geo") else None,
        "usuario_asignado": estado["usuario_asignado"],
        "usuario_intentado": estado.get("usuario_intentado"),
        "password_intentada": estado.get("password_intentada")
    }
       self.logger.guardar_evento(resumen)
       return "cerrar"
   
      self.historial.append(comando_norm)
      if len(self.historial) > 100:
            self.historial = self.historial[-100:]
   
      if comando_norm == "history":
             salida = ""
             for i, cmd in enumerate (self.historial, start=1):
                salida += f"{i} {cmd}\n"
             return salida   
   
      if comando_norm in RESPUESTAS:
         latencia = self.simulacion_de_latencia(comando_norm)  
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
             self.enviar_bloque(chan, str(salida))                        
      else:
        latencia = self.simulacion_de_latencia(comando_norm)
        respuesta = f"bash: {comando_norm}: command not found\n"
        self.enviar_bloque(chan, respuesta)
      
      if comando.startswith("echo"):
          contenido = comando.split(" ", 1)[1].encode("utf-8") if " " in comando else b""
          self.capturar_payload(estado, contenido, "echo_script")
      
      elif comando.startswith("cat >"):
          estado["capturando"] = True
          estado["buffer"] = []
          
      elif estado.get("capturando", False):
          if comando.strip() == "EOF":
              contenido = "\n".join(estado["buffer"]).encode("utf-8")
              self.capturar_payload(estado, contenido, "cat_script")
              estado["capturando"] = False
              estado["buffer"] = []
          else:
              estado["buffer"].append(comando)
    
      elif comando.startswith("./"):
           contenido = comando.encode("utf-8")
           self.capturar_payload(estado, contenido, "payload_executable")
           
      elif comando.lower().startswith(("wget", "curl")):
           partes = comando.split()
           for p in partes:
               if p.lower().startswith(("http://", "https://")):
                   self.capturar_payload(estado, p.encode("utf-8"), "payload_url")      
      
      self.logger.crear_evento({
          "timestamp": datetime.now().isoformat(timespec="seconds"),
          "ip":  estado["ip_remota"] if "ip_remota" in estado else None,
          "port": estado["port"] if "port" in estado else None,
          "evento": "comando",
          "usuario": estado["usuario"] if "usuario" in estado else None,
          "comando": comando,
          "session_id": estado["session_id"] if "session_id" in estado else None,
          "hostname_simulado": estado["hostname"],
          "sistema_simulado": estado["sistema"],
          "reverse_dns": estado.get("reverse_dns"),
          "pais": estado["geo"].get("pais") if estado.get("geo") else None,
          "region": estado["geo"].get("region") if estado.get("geo") else None,
          "ciudad": estado["geo"].get("ciudad") if estado.get("geo") else None,
          "isp": estado["geo"].get("isp") if estado.get("geo") else None,
          "asn": estado["geo"].get("asn") if estado.get("geo") else None,
          "usuario_asignado": estado["usuario_asignado"],
          "usuario_intentado": estado.get("usuario_intentado"),
          "password_intentada": estado.get("password_intentada")
      })
      
                                      
class HoneyLogger:
   
   """
     Esta clase va a servir para centralizar todos los logs del honeypot en un único espacio y darles un formato para leerlos con facilidad.
     Si luego se quieren analizar o hacer estadísticas estarán preparados para ello. 

   """
   
   def __init__(self, log_filename="logsHoneypot.csv", key_filename="host_rsa.key"):
      self.LOG_DIR = "logs"
      self.KEY_DIR = "keys"
      self.PAYLOAD_DIR = "payloads"
       
      os.makedirs(self.LOG_DIR, exist_ok=True)
      os.makedirs(self.KEY_DIR, exist_ok=True)
      os.makedirs(self.PAYLOAD_DIR, exist_ok=True)
    
      self.LOG_FILE = os.path.join(self.LOG_DIR, log_filename)
      self.KEY_FILE = os.path.join(self.KEY_DIR, key_filename)
      self.lock = threading.Lock()
      self.campos = [
            "timestamp", "ip", "port", "pais", "region", "ciudad", 
            "duracion", "frecuencia", "credencial", "isp",
            "asn", "reverse_dns", "hostname_simulado", "sistema_simulado", "evento", "timeout_inactividad"
            "usuario", "password", "comando", "usuario_asignado", "usuario_intentado", "password_intentada", "archivo", "hash", "tamano",
            "tipo_payload", "session_id", "echo_script", "cat_script", "payload_executable", "payload_url", "conexiones_activas", "thread"       ]
       
   def crear_evento(self, datos: dict) -> dict:
    fila = {
            "timestamp": datos.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            "ip": datos.get("ip") or None,
            "port": datos.get("port") or None,
            "pais": datos.get("pais") or None,
            "region": datos.get("region") or None,
            "ciudad": datos.get("ciudad") or None,
            "duracion": datos.get("duracion") or None,
            "frecuencia": datos.get("frecuencia") or None,
            "credencial": datos.get("credencial") or None,
            "isp": datos.get("isp") or None,
            "asn": datos.get("asn") or None,
            "reverse_dns": datos.get("reverse_dns") or None,
            "hostname_simulado": datos.get("hostname_simulado") or None,
            "sistema_simulado": datos.get("sistema_simulado") or None,
            "evento": datos.get("evento") or None,
            "timeout_inactividad": datos.get("timeout_inactividad") or None,
            "usuario": datos.get("usuario") or None,
            "password": datos.get("password") or None,
            "comando": datos.get("comando") or None,
            "usuario_asignado": datos.get("usuario_asignado") or None,
            "usuario_intentado": datos.get("usuario_intentado") or None,
            "password_intentada": datos.get("password_intentada") or None,
            "archivo": datos.get("archivo") or None,
            "hash": datos.get("hash") or None,
            "tamano": datos.get("tamano") or None,
            "tipo_payload": datos.get("tipo_payload") or None,
            "session_id": datos.get("session_id") or None,
            "echo_script": datos.get("echo_script") or None,
            "cat_script": datos.get("cat_script") or None,
            "payload_executable": datos.get("payload_executable") or None,
            "payload_url": datos.get("payload_url") or None,
            "conexiones_activas": datos.get("conexiones_activas") or None,
            "thread": threading.current_thread().name
    }
    self.guardar_evento(fila)
    return fila
    
   def guardar_evento(self, fila: dict) -> None:
       with self.lock:
            escribir_cabecera = not os.path.exists(self.LOG_FILE) or os.path.getsize(self.LOG_FILE) == 0
            with open(self.LOG_FILE, "a", newline="", encoding="UTF-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.campos, extrasaction="ignore")
                if escribir_cabecera:
                   writer.writeheader()
                writer.writerow(fila)     
            print(f"{fila.get('timestamp')} {fila.get('ip')}:{fila.get('port') or ''} registrado")     
   
if __name__ == "__main__":
    logger = HoneyLogger()
    hp = Honeypot("0.0.0.0", 22, logger)
    hp.iniciar()

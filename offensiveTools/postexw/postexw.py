from getpass import getpass
import platform
import subprocess
import re
from zipfile import Path
from requests_credssp.exceptions import AuthenticationException
import requests_credssp
import requests
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool


RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

CRITICO = RED + BOLD
CRITICO1 = YELLOW + BOLD

class Enumerador_Remoto:
    
    def __init__(self, host, usuario, puerto, contrasena):
        
        self.host = host
        self.usuario = usuario
        self.port = puerto
        self.contrasena = contrasena
        self.sesion = None # Aquí irá la conexion de WinRM
        self.shell = None 
        
        
    def construir_path(self, protocolo):
        
        path = f"{protocolo}://{self.host}:{self.port}/wsman"
        return path     
        
        
    def detectar_autenticacion(self):
        
        url= self.construir_path("http")
        
        try:
            
            respuesta = requests.get(url, verify=False, timeout=3)
            cabecera = respuesta.headers.get("WWW-Authenticate", "")
            metodos = [m.strip() for m in cabecera.split(",")]
            metodos = [m for m in metodos if m]
            return metodos
        except Exception:
            
            return []

    
    def combinacion_puertos(self):
        
        puerto = str(self.port).strip()
        
        combinaciones = []
        
        try: 
           combinaciones.append({"puerto": self.port, "ignore_ssl": False}) 
           combinaciones.append({"puerto": 5985, "ignore_ssl": False})
           combinaciones.append({"puerto": 5986, "ignore_ssl": True})
           combinaciones.append({"puerto": 80,  "ignore_ssl": False}) 
           combinaciones.append({"puerto": 443,  "ignore_ssl": True})
        except Exception as e:
            print("Error al combinar puertos: ", e)
            
        return combinaciones
    
    def crear_sesion(self, servidor, ignore_ssl, puerto):
        
        print("DEBUG crear_sesion: ", servidor, puerto, ignore_ssl)
        try:        
                    wsman = WSMan(
                    server=servidor,
                    port=int(puerto),
                    username=self.usuario,
                    password=self.contrasena,
                    ssl=ignore_ssl,
                    auth="ntlm")
                    pool = RunspacePool(wsman)
                    pool.open()
                    print("DEBUG crear_sesion: sesión creada correctamente")
                    return pool
        except Exception as e:
                print("DEBUG crear_sesion ERROR:", type(e).__name__, str(e))
                raise

        
    def probar_sesion(self, sesion):
    
      try:
          ps = PowerShell(sesion)
          ps.add_script("whoami")
          resultado = ps.invoke()
          if resultado:
            print("DEBUG resultado:", resultado)
            return True
        
          print("DEBUG resultado vacío")
          return False
      except Exception as e:
          print("DEBUG error:", e)
          return False
    
    def conector(self, crear_sesion, probar_sesion):
        print("DEBUG:", self.host, self.port)
        
        self.metodos_autenticacion = self.detectar_autenticacion()
        
        try:
            conexiones = self.combinacion_puertos()
            
            for conexion in conexiones:
                ignore_ssl = conexion["ignore_ssl"]
                self.port = conexion["puerto"]
                
                try:
                    
                    sesion = crear_sesion(self.host, ignore_ssl, self.port)
                
                except AuthenticationException:
                    continue
                except Exception:
                    continue
                
                if probar_sesion(sesion):
                    self.sesion = sesion
                    break
            else:
                print("No se pudo conseguir una conexión según las combinaciones existentes.")
        except Exception as e:
            print(f"{RED}No se pudo iniciar la conexión: {e}{RESET}")
        
    def listar_archivos(self):
        if self.sesion is None:
            print("No hay sesión WinRM activa. Ejecuta conector() primero.")
            return
        try:
                ps = PowerShell(self.sesion)
                ps.add_script(r'Get-ChildItem -Path C:\ -Recurse -Include *.config,*.xml,*.txt,*.ini,*.ps1 -ErrorAction SilentlyContinue |Select-String -Pattern "password|user|credential|root|key|/.htb" -SimpleMatch')
                resultado = ps.invoke()
                salida = resultado[0] if resultado else ""
                if resultado and resultado[0].output:
                        print(f"Se han encontrado posibles archivos que pueden ser de utilidad: \n {salida}")
                        print()
                else:
                        print()
                        print(f"{RED}No se han encontrado archivos de interés.{RESET}")
                        print()   
        except Exception as e:
            print(f"{RED}No se pudo ejecutar el comando en Powershell: {e}{RESET}")
            print() 
     
        
    def enumeracion_privilegios(self):
        if self.sesion is None:
            print("No hay sesión WinRM activa. Ejecuta conector() primero.")
            return
        ps = PowerShell(self.sesion)
        usuario_actual =  ps.add_script(r'whoami')
        resultado = ps.invoke()
        salida = resultado[0] if resultado else ""
        print()
        print(f"{YELLOW}Usuario aceptado: \n{RESET}", salida)
        print()
        
        ps = PowerShell(self.sesion)
        ps.add_script(r'$env:USERPROFILE')
        resultado = ps.invoke()
        path = resultado[0] if resultado else ""
        print()
        print(f"{YELLOW}Tu directorio actual es: \n{RESET}", path)
        print()
        
        ps = PowerShell(self.sesion)
        ps.add_script(r"whoami /priv | Out-String")
        resultado = ps.invoke()
        privilegios = resultado[0] if resultado else ""
        lineas = privilegios.splitlines()
        print()
        print(f"Los privilegios de esta máquina son: \n", privilegios)
        print()
        
        privilegios_interesantes = [
                                "SeBackupPrivilege",
                                "SeRestorePrivilege",
                                "SeTakeOwnershipPrivilege",
                                "SeDebugPrivilege",
                                "SeImpersonatePrivilege",
                                "SeAssignPrimaryTokenPrivilege",
                                "SeLoadDriverPrivilege",
                                "SeSystemEnvironmentPrivilege",
                                "SeManageVolumePrivilege",
                            ]
        
        print()
        print(f"{CRITICO1} Privilegios más interesantes encontrados: \n{RESET}")
        print(f"{BOLD} {'Privilegio':<30} {'Descripción':<50} {'Estado':<10} {RESET}")
        print(f"{'-'*30} {'-'*50} {'-'*10}")
        
        for linea in lineas:
            if any(p in linea for p in privilegios_interesantes):
                partes = linea.split()
                privilegio = partes[0]
                estado = partes[-1]
                descripcion = " ".join(partes[1:-1])
                
                if privilegio in privilegios_interesantes:
                    color = CRITICO
                    print(f"{color}{privilegio:<30} {descripcion:<50} {estado:<10}{RESET}")
                    print()


    def buscar_logs(self):
        
        if self.sesion is None:
            print("No hay sesión WinRM activa. Ejecuta conector() primero.")
            return
    
        try:
                ps = PowerShell(self.sesion)
                ps.add_script(r'Get-WinEvent -LogName Security | Where-Object { $_.Id -in 4624, 4625, 4634, 4672, 4688 } | ForEach-Object {if (($_ | Out-String) -match "user|password|root|\.htb") {$_ | Format-Table TimeCreated, Id, Message -Autosize}}')
                resultado = ps.invoke()
                salida = resultado[0] if resultado else ""
                print()
                print("Estos han sido los logs del sistema encontrados: ", salida)
                print()
        except Exception as e:
                print(f"{RED}No se pudo ejecutar el comando en Powershell y leer logs: {e}{RESET}")
                print()
            

    def buscar_directorios(self):

        rutas = [
            r'C:\inetpub\wwwroot\web.config',
            r'C:\Windows\Microsoft.NET\Framework*\config\web.config',
            r'C:\ProgramData\*',
            r'C:\Windows\Panther\Unattend.xml',
            r'C:\Windows\System32\Sysprep\Unattend.xml',
            r'C:\Windows\System32\Sysprep\Sysprep.xml'
        ]

        if self.sesion is None:
            print("No hay sesión WinRm activa. Ejecuta conector() primero.")
            return

        # --- BLOQUE A: rutas fijas ---
        for ruta in rutas:
            try:
                ps = PowerShell(self.sesion)
                comando = ps.add_script(fr'''
        Get-ChildItem -Path "{ruta}" -Recurse -Include *.txt,*.xml,*.config,*.ini,*.ps1 -ErrorAction SilentlyContinue |
        Select-String -Pattern "password","user","credential","root","key","/.htb" -SimpleMatch
    ''')
                resultado = ps.invoke()

                if resultado and resultado[0]:
                    print(f"\n[+] Archivos sensibles encontrados en: {ruta}\n{resultado[0]}\n")
                else:
                    print(f"[-] No se han encontrado archivos sensibles en: {ruta}")

            except Exception as e:
                print(f"{RED}No se pudo ejecutar el comando en Powershell: {e}{RESET}\n")

        # --- BLOQUE B: perfiles de usuario ---
        ps = PowerShell(self.sesion)
        comando = ps.add_script(fr"""
    Get-ChildItem C:\Users\ -Directory | ForEach-Object {{
        $roaming = "$($_.FullName)\AppData\Roaming"
        if (Test-Path $roaming) {{
            Get-ChildItem -Path $roaming -Recurse -Include *.txt,*.xml,*.config,*.ini,*.ps1 -ErrorAction SilentlyContinue |
                Select-String -Pattern 'password','user','credential','root','key','/.htb' -SimpleMatch |
                ForEach-Object {{ "[SENSIBLE] $($_.Path)" }}
        }}

        $local = "$($_.FullName)\AppData\Local"
        if (Test-Path $local) {{
            Get-ChildItem -Path $local -Recurse -Include *.txt,*.xml,*.config,*.ini,*.ps1 -ErrorAction SilentlyContinue |
                Select-String -Pattern 'password','user','credential','root','key','/.htb' -SimpleMatch |
                ForEach-Object {{ "[SENSIBLE] $($_.Path)" }}
        }}
        if (Test-Path $roaming) {{
            Get-ChildItem -Path $roaming -Recurse -Include *.txt -ErrorAction SilentlyContinue |
                ForEach-Object {{ "[TXT] $($_.FullName)" }}
        }}

        if (Test-Path $local) {{
            Get-ChildItem -Path $local -Recurse -Include *.txt -ErrorAction SilentlyContinue |
                ForEach-Object {{ "[TXT] $($_.FullName)" }}
        }}
    }}
    """
        )

        resultado = ps.invoke()

        print("\n=== Resultados en perfiles de usuario ===")
        print(resultado[0] if resultado else "No se encontraron archivos.")
   
if __name__ == "__main__":         
    Introducir_host = input("Introduce el host: ")
    Introducir_puerto = input("Introduce el puerto: ") 
    Introducir_usuario = input("Introduce el usuario: ")
    Introducir_contraseña = getpass("Introduce la contraseña: ")
    
    cliente = Enumerador_Remoto(Introducir_host, Introducir_usuario, Introducir_puerto, Introducir_contraseña)
    
    cliente.detectar_autenticacion()
    cliente.combinacion_puertos()
    cliente.conector(cliente.crear_sesion, 
                     cliente.probar_sesion)
    cliente.listar_archivos()
    cliente.buscar_directorios()
    cliente.enumeracion_privilegios()
    cliente.buscar_logs()
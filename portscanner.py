import socket
from concurrent.futures import ThreadPoolExecutor
import subprocess
import re
import ipaddress


#lista compartida
resultados = []

#Herramienta para tratar de encontrar el os (no es muy precisa pero tratare de actualizar o cambiarla con el tiempo)

def detectar_os(ip):
    try:
        resultado = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True,
            text=True
        )
        ttl_match = re.search(r"ttl=(\d+)", resultado.stdout, re.IGNORECASE)
        if ttl_match:
            ttl = int(ttl_match.group(1))
            if ttl == 64:
                return f"Linux / Mac (TTL={ttl}) [Confianza: Alta]"
            elif 60 <= ttl < 64:
                return f"Linux / Mac (TTL={ttl}) [Confianza: Media]"
            elif ttl == 128:
                return f"Windows (TTL={ttl}) [Confianza: Alta]"
            elif 120 <= ttl < 128:
                return f"Windows (TTL={ttl}) [Confianza: Media]"
            elif ttl == 255:
                return f"Cisco / Router (TTL={ttl}) [Confianza: Alta]"
            else:
                return f"OS desconocido (TTL={ttl}) [Confianza: Baja]"
        return "OS desconocido [Confianza: Baja]"
    except Exception:
        return "OS desconocido [Confianza: Baja]"


def escanear_puerto(ip, puerto):
    try:
        #Voy a usar with para el socket se cierre automaticamente cuando termine
     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.settimeout(1) #Esto es para configurar cuanto va a esperar el script por cada puerto 
      result = sock.connect_ex((ip, puerto))
    
      if result == 0:
          banner = "Desconocido (No envio saludo)"
          try:
           banner_bytes = sock.recv(1024)
           if banner_bytes:
              banner = banner_bytes.decode('utf-8', errors='ignore').strip()
          except socket.timeout:
              servicios_comunes = {80: "HTTP (Web)", 443: "HTTPS (Web segura)", 21: "FTP", 22: "SSH", 23:"Telnet"}
              banner = servicios_comunes.get(puerto, "Servicio desconocido (Timeout)")
         
          print(f"[+] Puerto {puerto} Abierto -> Servicio: {banner}")
          resultados.append(f"Puerto {puerto} Abierto -> Servicio: {banner}")
    
    except Exception:
    #Si llega a haber un error de red o interrupcion pues solo se ignora para no romper el bucle 
         pass

def descubrir_hosts(red):
    print(f"\nDescubriendo hosts activos en {red}...")
    hosts_activos = []
    red_obj = ipaddress.IPv4Network(red, strict=False)

    def ping_host(ip):
        resultado = subprocess.run(
            ["ping", "-c", "1", "-W", "1", str(ip)],
            capture_output=True
            )
        if resultado.returncode == 0:
            hosts_activos.append(str(ip))
            print(f"[+] Hosts activo: {ip}")

    with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(ping_host, red_obj.hosts())

    return hosts_activos    



def main():
    #Esta parte es para la nueva opcion, bueno a lo de escanear la red completa
    print("\nQue queres hacer?")
    print("1. Escanear una IP especifica")
    print("2. Escanear una red completa")
    modo = input("Seleciona una opcion (1 o 2): ")

    if modo == "2":
        red = input("Ingrese la red (ej: 192.168.11.0/24): ")
        hosts = descubrir_hosts(red)
    if not hosts:
        print("No se encontraron hosts activos.")
        return
    print(f"\nHosts activos encontrados: {len(hosts)}")
    for host in hosts:
        print(f"\nEscaneando {host}...")
        os_detectado = detectar_os(host)
        with ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(lambda p: escanear_puerto(host, p), range(1, 1024))
        print(f"OS probable: {os_detectado}")

    else:
        ip = input("Ingrese la direccion IP a escanear: ")
    #agregado para la deteccion de OS
        os_detectado = detectar_os(ip)
    #Cambio para tener la opcion de esenciales y completo
        print("\nQue tipo de escaneo queres realizar?")
        print("1. Escaneo rapido (Puertos 1 al 1,024)")
        print("2. Escaneo completo (Todos los puertos)")
        opcion = input("Seleciona una opcion (1 o 2): ")

    #
    if opcion == "2":
     puertos = range(1, 65536)
     print("\nModo seleccionado: Escaneo Completo (65536 puertos).")

    else:
     puertos = range(1, 1024)
     print("\nModo seleccionado: Escaneo Rapido (1024 puertos)")

    print(f"Iniciando escaneo en {ip}...")
    print("------------------------------------")

    with ThreadPoolExecutor(max_workers=100) as  executor:
        executor.map(lambda p: escanear_puerto(ip, p), puertos)

    print("-------------------------")
    print("Escaneo finalizado")

    print(f"\n--- Reporte final ---")
    print(f"IP escaneada: {ip}")
    print(f"OS probable: {os_detectado}")
    print(f"Puertos abiertos: {len(resultados)}")

    with open("resultados.txt", "w") as archivo:
        archivo.write(f"Resultados del escaneo en {ip}\n")
        archivo.write(f"OS probable: {os_detectado}\n")
        archivo.write("=" * 40 + "\n")
        for resultado in resultados:
            archivo.write(resultado + "\n")

    print(f"Resultados guardados en resultados.txt")
     


if __name__== "__main__":
    main()



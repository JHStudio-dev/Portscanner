import socket
from concurrent.futures import ThreadPoolExecutor
import subprocess
import re


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
            if ttl <= 64:
                return f"Linux / Mac (TTL={ttl})"
            elif ttl <= 128:
                return f"Windows(TTL={ttl})"
            else:
                return f"Cisco / Router (TTL={ttl})"
            return "OS desconocido"
    except Exception:
            return "OS desconocido"

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

def main():
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



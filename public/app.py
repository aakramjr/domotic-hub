import RPi.GPIO as GPIO
from time import sleep
import signal 
import sys
import firebase_admin
from firebase_admin import credentials, firestore
import threading

#1 configuracion de hardware 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pines_habitaciones = {
    'salon': 27,
    'cocina': 22,
    'banio' : 17,
    'habitacion1': 6
}

def limpiar_y_salir(sig, frame):
    print("\nCerrando servidor, limpiando GPIO y apagando luces.")
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, limpiar_y_salir)

def apagar_todo(nivel):
    for pin in pines_habitaciones.values():
        GPIO.output(pin, nivel)
    print(f"HARDWARE: Todas las luces -> {'Encendidas' if nivel else 'Apagadas'}")

def encender_todo(nivel):
    for pin in pines_habitaciones.values():
        GPIO.output(pin, nivel)
    print(f"HARDWARE: Todas las luces -> {'Encendidas' if nivel else 'Apagadas'}")

# configurar todos los pines definidos en el diccionario como salida y apagarlos
for pin in pines_habitaciones.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def hardware_controlar_luz(habitacion, estado):
    nivel = GPIO.HIGH if estado else GPIO.LOW
    print(f"DEBUG: Recibida orden para '{habitacion}' -> {'Encender' if estado else 'Apagar'} (Nivel GPIO: {nivel})")

    if habitacion == 'todas':
        if estado: 
            encender_todo(nivel)
        else:      
            apagar_todo(nivel)
        return 
        
    if habitacion in pines_habitaciones:
        pin = pines_habitaciones[habitacion]
        GPIO.output(pin, nivel)
        print(f"HARDWARE: Luz '{habitacion}' (Pin {pin}) -> {'Encendido' if estado else 'Apagado'}")
    else:
        print(f"ADVERTENCIA: Habitación '{habitacion}' no reconocida.")


# 2. Firebase cloud

print("Conectando a la nube de Firebase...")

cred = credentials.Certificate("domotic-hub-10c05-firebase-adminsdk-fbsvc-2879df49b1.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()
print("¡Conectado a la base de datos correctamente!")

def on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        # Si alguien toca un botón en tu web (desde cualquier lugar del mundo)
        if change.type.name == 'ADDED' or change.type.name == 'MODIFIED':
            doc = change.document
            datos = doc.to_dict()
            habitacion = doc.id 
            estado = datos.get('estado', False)
            
            # Ejecutamos tu función original de hardware
            hardware_controlar_luz(habitacion, estado)

# Se queda escuchando la colección "luces" 24/7
coleccion_luces = db.collection('luces')
watch = coleccion_luces.on_snapshot(on_snapshot)

if __name__ == '__main__':
    try:
        print("SISTEMA ACTIVO: Esperando órdenes desde tu app web en el móvil...")
        # Esto mantiene el script vivo sin consumir apenas recursos
        evento = threading.Event()
        evento.wait()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
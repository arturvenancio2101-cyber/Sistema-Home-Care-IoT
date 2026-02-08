Este script, executado no Raspberry Pi Zero W, lê o estado do pino digital do sensor e publica a informação num tópico MQTT.
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

# --- CONFIGURAÇÕES ---
PIN_GAS = 23
MQTT_BROKER = "192.168.0.107" # IP do Home Assistant
MQTT_PORT = 1883
MQTT_TOPIC_ESTADO = "gas/detector/estado"
MQTT_USER = "Homecareieb"
MQTT_PASSWORD = "ieb12345"
PAYLOAD_DETECTED = "DETECTED"
PAYLOAD_CLEAR = "CLEAR"

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Detetor de Gás: Conectado ao Broker MQTT!")
        # Publica o estado inicial "CLEAR" assim que conecta
        client.publish(MQTT_TOPIC_ESTADO, PAYLOAD_CLEAR, retain=True)
    else:
        print(f"Detetor de Gás: Falha ao conectar, código: {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi_detector_gas")
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_GAS, GPIO.IN)

print("Iniciando monitoramento de gás...")
estado_anterior = ""

try:
    while True:
        # A saída D0 do sensor fica em HIGH (1) normalmente e vai para LOW (0) quando deteta gás.
        if GPIO.input(PIN_GAS) == GPIO.LOW:
            estado_atual = "DETECTADO"
            payload_atual = PAYLOAD_DETECTED
        else:
            estado_atual = "LIMPO"
            payload_atual = PAYLOAD_CLEAR
            
        if estado_atual != estado_anterior:
            print(f"Estado do Gás mudou para: {estado_atual}")
            client.publish(MQTT_TOPIC_ESTADO, payload_atual, retain=True)
            estado_anterior = estado_atual
            
        time.sleep(2)
except KeyboardInterrupt:
    print("\nMonitoramento de gás interrompido.")
finally:
    GPIO.cleanup()
    client.loop_stop()

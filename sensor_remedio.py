Este script implementa um filtro de mediana para estabilizar as leituras do sensor, lê a distância e publica o estado (OPEN ou CLOSED) via MQTT.
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import statistics

# --- CONFIGURAÇÕES ---
DISTANCIA_FECHADA_MAX = 12.0 # Distância em cm para considerar a caixa fechada
PIN_TRIGGER = 17
PIN_ECHO = 18
MQTT_BROKER = "192.168.0.107"
MQTT_PORT = 1883
MQTT_TOPIC_ESTADO = "remedio/caixa/estado"
MQTT_USER = "Homecareieb"
MQTT_PASSWORD = "ieb12345"
PAYLOAD_OPEN = "OPEN"
PAYLOAD_CLOSED = "CLOSED"

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Conectado ao Broker MQTT com sucesso!")
        client.publish(MQTT_TOPIC_ESTADO, PAYLOAD_CLOSED, retain=True) # Publica estado inicial
    else:
        print(f"Falha ao conectar, código: {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi_caixa_remedio")
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)

estado_anterior = ""

def medir_distancia_estabilizada():
    leituras = []
    for _ in range(5): # Faz 5 leituras
        GPIO.output(PIN_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(PIN_TRIGGER, False)
        start_time = time.time()
        stop_time = time.time()
        timeout_start = time.time()
        while GPIO.input(PIN_ECHO) == 0:
            start_time = time.time()
            if time.time() - timeout_start > 0.1: return -1
        while GPIO.input(PIN_ECHO) == 1:
            stop_time = time.time()
            if time.time() - timeout_start > 0.1: return -1
        distance = ((stop_time - start_time) * 34300) / 2
        if 0 < distance < 400: leituras.append(distance)
        time.sleep(0.05)
    if len(leituras) > 0:
        return statistics.median(leituras) # Retorna a mediana
    return -1

try:
    while True:
        dist = medir_distancia_estabilizada()
        if dist != -1:
            estado_atual = "OPEN" if dist > DISTANCIA_FECHADA_MAX else "CLOSED"
            if estado_atual != estado_anterior:
                print(f"Estado mudou para: {estado_atual} (Distância: {dist:.1f} cm)")
                client.publish(MQTT_TOPIC_ESTADO, estado_atual, retain=True)
                estado_anterior = estado_atual
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    client.loop_stop()

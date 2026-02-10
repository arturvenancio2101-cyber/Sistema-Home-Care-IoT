import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

# --- CONFIGURAÇÕES GERAIS ---
# Ajuste estas variáveis conforme o seu ambiente
PIN_GAS = 23  # Pino GPIO BCM onde o sensor está conectado

# --- CONFIGURAÇÕES MQTT ---
MQTT_BROKER = "192.168.1.X"      # IP do seu servidor Home Assistant / Broker
MQTT_PORT = 1883                 # Porta padrão MQTT
MQTT_TOPIC_ESTADO = "gas/detector/estado"
MQTT_USER = "seu_usuario_mqtt"   # Ex: homeassistant
MQTT_PASSWORD = "sua_senha_mqtt" # Ex: senha123
PAYLOAD_DETECTED = "DETECTED"
PAYLOAD_CLEAR = "CLEAR"

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Detetor de Gás: Conectado ao Broker MQTT!")
        # Publica o estado inicial "CLEAR" assim que conecta
        client.publish(MQTT_TOPIC_ESTADO, PAYLOAD_CLEAR, retain=True)
    else:
        print(f"Detetor de Gás: Falha ao conectar, código: {rc}")

# Configuração do Cliente
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi_detector_gas")
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"Erro ao conectar no MQTT: {e}")

# Configuração GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_GAS, GPIO.IN)

print("Iniciando monitoramento de gás...")
estado_anterior = ""

try:
    while True:
        # A saída D0 do sensor fica em HIGH (1) normalmente e vai para LOW (0) quando deteta gás.
        # Ajuste a sensibilidade no potenciômetro do sensor se necessário.
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

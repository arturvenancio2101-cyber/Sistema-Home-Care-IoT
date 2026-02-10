import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import statistics

# --- CONFIGURAÇÕES DO AMBIENTE (PREENCHA AQUI) ---
# Ajuste estes pinos conforme a sua montagem física no Raspberry Pi
PIN_TRIGGER = 17
PIN_ECHO = 18
DISTANCIA_FECHADA_MAX = 12.0 # Distância em cm para considerar a caixa fechada

# --- CONFIGURAÇÕES MQTT ---
MQTT_BROKER = "192.168.1.X"       # IP do seu servidor Home Assistant
MQTT_PORT = 1883
MQTT_TOPIC_ESTADO = "remedio/caixa/estado"
MQTT_USER = "seu_usuario_mqtt"    # Ex: mqtt_user
MQTT_PASSWORD = "sua_senha_mqtt"  # Ex: senha_segura
PAYLOAD_OPEN = "OPEN"
PAYLOAD_CLOSED = "CLOSED"

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Sensor Remédio: Conectado ao Broker MQTT com sucesso!")
        # Publica estado inicial como fechado por segurança ao iniciar
        client.publish(MQTT_TOPIC_ESTADO, PAYLOAD_CLOSED, retain=True)
    else:
        print(f"Falha ao conectar, código: {rc}")

# Configuração do Cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi_caixa_remedio")
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"Erro ao conectar no MQTT: {e}")

# Configuração GPIO (Boardcom)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)

estado_anterior = ""

def medir_distancia_estabilizada():
    """
    Realiza 5 leituras rápidas do sensor ultrassônico e retorna a mediana.
    Isso filtra ruídos e leituras falsas comuns em sensores HC-SR04.
    """
    leituras = []
    for _ in range(5): 
        # Pulso de Trigger
        GPIO.output(PIN_TRIGGER, True)
        time.sleep(0.00001)
        GPIO.output(PIN_TRIGGER, False)
        
        start_time = time.time()
        stop_time = time.time()
        timeout_start = time.time()
        
        # Aguarda o Echo iniciar (Low -> High)
        while GPIO.input(PIN_ECHO) == 0:
            start_time = time.time()
            if time.time() - timeout_start > 0.1: break # Timeout de segurança

        # Aguarda o Echo terminar (High -> Low)
        while GPIO.input(PIN_ECHO) == 1:
            stop_time = time.time()
            if time.time() - timeout_start > 0.1: break # Timeout de segurança
            
        # Cálculo da distância (Velocidade do som = 34300 cm/s)
        distance = ((stop_time - start_time) * 34300) / 2
        
        # Filtra valores absurdos (sensor tem alcance de 2cm a 400cm)
        if 0 < distance < 400: 
            leituras.append(distance)
        
        time.sleep(0.05) # Pequena pausa entre leituras
        
    if len(leituras) > 0:
        return statistics.median(leituras) # Retorna a mediana estatística
    return -1

print("Iniciando monitoramento da caixa de remédios...")

try:
    while True:
        dist = medir_distancia_estabilizada()
        
        if dist != -1:
            # Lógica de histerese simples: Se maior que X, está aberta.
            estado_atual = "OPEN" if dist > DISTANCIA_FECHADA_MAX else "CLOSED"
            
            # Só publica no MQTT se o estado mudou (evita spam na rede)
            if estado_atual != estado_anterior:
                print(f"Estado mudou para: {estado_atual} (Distância média: {dist:.1f} cm)")
                client.publish(MQTT_TOPIC_ESTADO, estado_atual, retain=True)
                estado_anterior = estado_atual
                
        time.sleep(1) # Verifica a cada 1 segundo

except KeyboardInterrupt:
    print("\nMonitoramento interrompido.")

finally:
    GPIO.cleanup()
    client.loop_stop()

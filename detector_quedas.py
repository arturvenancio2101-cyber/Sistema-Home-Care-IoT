# Versão final, otimizada para rodar em modo "backend" sem interface gráfica.
from cvzone.PoseModule import PoseDetector
import cv2
import paho.mqtt.client as mqtt
import time

# --- CONFIGURAÇÕES E VARIÁVEIS (iguais à V2) ---
MQTT_BROKER = "192.168.0.107"
MQTT_PORT = 1883
MQTT_TOPIC = "seguranca/quedadetectada"
MQTT_USER = "Homecareieb"
MQTT_PASSWORD = "ieb12345"
alerta_ativo = False
FRAME_SKIP = 3
LIMITE_ALTURA_QUEDA = 600
USUARIO_RTSP = "admin"
SENHA_RTSP = "ieb12345"
IP_CAMERA = "192.168.0.105"
URL_DO_STREAM = f"rtsp://{USUARIO_RTSP}:{SENHA_RTSP}@{IP_CAMERA}/V_ENC_000"

# --- Conexão MQTT ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print(f"Conexão MQTT estabelecida com sucesso.")
except Exception as e:
    print(f"ERRO DE CONEXÃO MQTT: {e}.")
    exit()

# --- Conexão Vídeo ---
video = cv2.VideoCapture(URL_DO_STREAM)
if not video.isOpened():
    print(f"ERRO: Não foi possível abrir o stream de vídeo.")
    client.loop_stop()
    exit()

detector = PoseDetector()
print("Detector de quedas iniciado em modo backend.")

while True:
    check, img = video.read()
    if not check:
        # Lógica de reconexão
        print("Aviso: Falha na leitura do frame. Tentando reconectar...")
        video.release()
        time.sleep(5) # Pausa antes de tentar reconectar
        video = cv2.VideoCapture(URL_DO_STREAM)
        continue

    if int(video.get(cv2.CAP_PROP_POS_FRAMES)) % FRAME_SKIP != 0:
        continue

    # O processamento ocorre sem a exibição de imagem
    resultado = detector.findPose(img, draw=False)
    pontos, bbox = detector.findPosition(img, draw=False)

    queda_detectada_neste_frame = False
    
    if len(pontos) >= 1:
        cabeca = pontos[0][1]
        quadril_y = int((pontos[23][1] + pontos[24][1]) / 2)

        quadril_muito_baixo = quadril_y >= LIMITE_ALTURA_QUEDA
        corpo_horizontalizado = (quadril_y - cabeca) <= 50

        if quadril_muito_baixo and corpo_horizontalizado:
            queda_detectada_neste_frame = True
            if not alerta_ativo:
                print(f"--- QUEDA DETECTADA! ENVIANDO ALERTA ---")
                client.publish(MQTT_TOPIC, "QUEDA")
                alerta_ativo = True

    if not queda_detectada_neste_frame and alerta_ativo:
        print("Alerta resetado. Pronto para detectar a próxima queda.")
        alerta_ativo = False

# Este loop não tem 'break' intencional para rodar indefinidamente.
# A interrupção seria feita pelo sistema operativo (ex: Ctrl+C ou parando o serviço).

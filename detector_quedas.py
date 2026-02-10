# Versão final, otimizada para rodar em modo "backend" sem interface gráfica.
from cvzone.PoseModule import PoseDetector
import cv2
import paho.mqtt.client as mqtt
import time

# --- CONFIGURAÇÕES DO AMBIENTE (PREENCHA AQUI) ---
# Configurações do Broker MQTT (Home Assistant)
MQTT_BROKER = "192.168.1.X"       # IP do seu servidor Home Assistant
MQTT_PORT = 1883
MQTT_TOPIC = "seguranca/quedadetectada"
MQTT_USER = "seu_usuario_mqtt"    # Ex: mqtt_user
MQTT_PASSWORD = "sua_senha_mqtt"  # Ex: senha_segura

# Configurações da Câmera IP (RTSP)
IP_CAMERA = "192.168.1.Y"         # IP da sua câmera de segurança
USUARIO_RTSP = "admin"            # Usuário da câmera
SENHA_RTSP = "senha_da_camera"    # Senha da câmera
# Ajuste o final da URL (/V_ENC_000) conforme o modelo da sua câmera (Ex: onvif, ch01, etc)
URL_DO_STREAM = f"rtsp://{USUARIO_RTSP}:{SENHA_RTSP}@{IP_CAMERA}/V_ENC_000"

# Parâmetros de Detecção
FRAME_SKIP = 3             # Processar 1 a cada X frames para economizar CPU
LIMITE_ALTURA_QUEDA = 600  # Ajuste conforme a altura da instalação da câmera
alerta_ativo = False

# --- Conexão MQTT ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print(f"Conexão MQTT estabelecida com sucesso.")
except Exception as e:
    print(f"ERRO DE CONEXÃO MQTT: {e}. Verifique o IP e as credenciais.")
    exit()

# --- Conexão Vídeo ---
video = cv2.VideoCapture(URL_DO_STREAM)
if not video.isOpened():
    print(f"ERRO: Não foi possível abrir o stream de vídeo em {IP_CAMERA}.")
    client.loop_stop()
    exit()

detector = PoseDetector()
print("Detector de quedas iniciado em modo backend.")

try:
    while True:
        check, img = video.read()
        
        # Lógica de reconexão automática em caso de queda do sinal de vídeo
        if not check:
            print("Aviso: Falha na leitura do frame. Tentando reconectar...")
            video.release()
            time.sleep(5) # Pausa antes de tentar reconectar
            video = cv2.VideoCapture(URL_DO_STREAM)
            continue

        # Pular frames para otimizar processamento no Raspberry Pi
        if int(video.get(cv2.CAP_PROP_POS_FRAMES)) % FRAME_SKIP != 0:
            continue

        # O processamento ocorre sem a exibição de imagem (Headless)
        resultado = detector.findPose(img, draw=False)
        pontos, bbox = detector.findPosition(img, draw=False)

        queda_detectada_neste_frame = False
        
        if len(pontos) >= 1:
            # Ponto 0 = Nariz/Cabeça
            # Pontos 23 e 24 = Quadris (Esquerdo e Direito)
            cabeca = pontos[0][1]
            quadril_y = int((pontos[23][1] + pontos[24][1]) / 2)

            # Lógica simples de queda:
            # 1. O quadril está muito baixo (perto do chão/base da imagem)
            # 2. A diferença de altura entre quadril e cabeça é pequena (corpo na horizontal)
            quadril_muito_baixo = quadril_y >= LIMITE_ALTURA_QUEDA
            corpo_horizontalizado = abs(quadril_y - cabeca) <= 50

            if quadril_muito_baixo and corpo_horizontalizado:
                queda_detectada_neste_frame = True
                if not alerta_ativo:
                    print(f"--- QUEDA DETECTADA! ENVIANDO ALERTA ---")
                    client.publish(MQTT_TOPIC, "QUEDA")
                    alerta_ativo = True

        # Reset do alerta se a pessoa se levantar ou a detecção parar
        if not queda_detectada_neste_frame and alerta_ativo:
            print("Situação normalizada. Resetando alerta.")
            alerta_ativo = False

except KeyboardInterrupt:
    print("\nEncerrando detector de quedas...")

finally:
    video.release()
    client.loop_stop()
    print("Sistema encerrado com segurança.")

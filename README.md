# Sistema de Monitoramento Home Care Inteligente 🏥🏠

Projeto de Engenharia Eletrônica desenvolvido durante estágio no Instituto de Engenharia Biomédica (IEB-UFSC). O objetivo foi criar um sistema modular para monitorar a segurança de idosos em casa.

## 🚀 Funcionalidades

### 1. Detecção de Quedas (Visão Computacional)
Sistema capaz de identificar quedas em tempo real utilizando uma câmera IP.
- **Tecnologia:** Python, OpenCV e cvzone (PoseModule).
- **Lógica:** Analisa a posição do esqueleto (cabeça vs. joelhos/quadril) para identificar a queda horizontal.
- **Integração:** Envia alertas via MQTT para o servidor central.

### 2. Caixa de Remédios Inteligente
Monitora a adesão medicamentosa do paciente.
- **Hardware:** Raspberry Pi Zero W e Sensor Ultrassônico (HC-SR04).
- **Lógica:** Detecta a abertura da caixa e envia o status (OPEN/CLOSED) para o sistema.
- **Software:** Filtro de mediana implementado para estabilizar leituras do sensor.

### 3. Detector de Gás e Segurança
Monitoramento ambiental passivo.
- **Sensor:** Série MQ (Gás/Fumaça).
- **Alerta:** Dispara notificações críticas no celular e avisos sonoros na Alexa em caso de vazamento.

## 🛠 Tecnologias e Ferramentas
- **Linguagem:** Python 3
- **Plataforma IoT:** Home Assistant OS
- **Comunicação:** Protocolo MQTT (Paho-MQTT)
- **Hardware:** Raspberry Pi 3, Raspberry Pi Zero W, ESP32
- **Bibliotecas:** `cvzone`, `opencv-python`, `RPi.GPIO`

## 📋 Como executar
Este projeto foi desenhado para rodar em um ambiente distribuído (Sensores via Raspberry Pi Zero W comunicando com servidor central Home Assistant). Os scripts Python nos arquivos deste repositório devem ser executados nos respectivos dispositivos de borda.

### 🎥 Demonstração do Projeto

[![Assista ao vídeo](https://www.youtube.com/watch?v=XDO5FzYNTe4)](https://youtube.com/shorts/LbA6UpkCn2g?si=-O37LMx2275_IpyP)

> Clique na imagem acima para ver a detecção de quedas e o alerta na Alexa em funcionamento.


---
*Autor: Artur Venancio Pacheco - Estudante de Engenharia Eletrônica UFSC*

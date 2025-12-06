# Dockerfile otimizado para GitHub Actions (menor uso de espaço)
FROM python:3.10-slim

WORKDIR /app

# Instalar apenas dependências essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    libxrender-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Criar usuário não-root
RUN useradd -m -u 1000 appuser

# Copiar requirements.txt primeiro (melhor cache)
COPY requirements.txt .

# Instalar dependências Python em camadas para otimizar espaço
# Instalar apenas o essencial para o GitHub Actions
RUN pip install --no-cache-dir --user \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install --no-cache-dir --user \
    transformers==4.35.0 \
    tensorflow-cpu==2.15.0 \
    ultralytics==8.0.200 \
    opencv-python==4.8.1.78 \
    librosa==0.10.1 \
    soundfile==0.12.1 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    numpy==1.24.3 \
    pillow==10.1.0 \
    scikit-learn==1.3.2 \
    matplotlib==3.8.2 \
    seaborn==0.13.0 \
    pandas==2.1.3 \
    scipy==1.11.4

# Limpar cache do pip
RUN pip cache purge

# Copiar modelo YOLO (apenas o essencial)
COPY --chown=appuser:appuser yolov8n.pt .

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Criar diretório temporário
RUN mkdir -p temp_videos_ia && chown -R appuser:appuser /app

# Configurar PATH para incluir pacotes do usuário
ENV PATH=/home/appuser/.local/bin:$PATH

# Expor porta
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Mudar para usuário não-root
USER appuser

# Comando para executar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
#!/bin/bash

# 🔧 Script de Preparação de Bundle Completo para Linux
# Este script prepara todos os recursos necessários para build Tauri completo

set -e

echo "🚀 Iniciando preparação de bundle completo..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar Docker
log "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker não encontrado. Instale o Docker primeiro."
fi

# Verificar espaço em disco
log "Verificando espaço em disco..."
AVAILABLE=$(df . | tail -1 | awk '{print $4}')
REQUIRED=$((10 * 1024 * 1024)) # 10GB em KB
if [ $AVAILABLE -lt $REQUIRED ]; then
    warn "Espaço em disco pode ser insuficiente. Recomendado: 10GB+"
fi

# Criar estrutura de diretórios
log "Criando estrutura de diretórios..."
mkdir -p Globo-Front-main/src-tauri/resources/docker-images
mkdir -p Globo-Front-main/src-tauri/resources/residencia4-backend-master
mkdir -p Globo-Front-main/src-tauri/resources/residencia4-ia-main

# Copiar arquivos de configuração
log "Copiando arquivos de configuração..."
cp docker-compose.yml Globo-Front-main/src-tauri/resources/ || error "Falha ao copiar docker-compose.yml"
cp .env Globo-Front-main/src-tauri/resources/ || error "Falha ao copiar .env"

# Copiar backend completo
log "Copiando backend completo..."
if [ -d "residencia4-backend-master" ]; then
    cp -r residencia4-backend-master/* Globo-Front-main/src-tauri/resources/residencia4-backend-master/ || warn "Falha ao copiar backend"
else
    warn "Diretório residencia4-backend-master não encontrado"
fi

# Copiar serviço IA completo
log "Copiando serviço IA..."
if [ -d "residencia4-ia-main" ]; then
    cp -r residencia4-ia-main/* Globo-Front-main/src-tauri/resources/residencia4-ia-main/ || warn "Falha ao copiar serviço IA"
else
    warn "Diretório residencia4-ia-main não encontrado"
fi

# Build e exportar imagens Docker
log "Construindo imagens Docker..."

# PostgreSQL (imagem oficial)
if [ ! -f "Globo-Front-main/src-tauri/resources/docker-images/postgres.tar" ]; then
    log "Baixando e exportando PostgreSQL..."
    docker pull postgres:15-alpine
    docker save postgres:15-alpine -o Globo-Front-main/src-tauri/resources/docker-images/postgres.tar
    log "PostgreSQL exportado ($(du -h Globo-Front-main/src-tauri/resources/docker-images/postgres.tar | cut -f1))"
else
    log "PostgreSQL já existe, pulando..."
fi

# Backend API
if [ -d "residencia4-backend-master" ]; then
    if [ ! -f "Globo-Front-main/src-tauri/resources/docker-images/backend.tar" ]; then
        log "Construindo e exportando Backend API..."
        cd residencia4-backend-master
        docker build -t globo-backend:latest .
        docker save globo-backend:latest -o ../Globo-Front-main/src-tauri/resources/docker-images/backend.tar
        cd ..
        log "Backend API exportado ($(du -h Globo-Front-main/src-tauri/resources/docker-images/backend.tar | cut -f1))"
    else
        log "Backend API já existe, pulando..."
    fi
fi

# IA Service
if [ -d "residencia4-ia-main" ]; then
    if [ ! -f "Globo-Front-main/src-tauri/resources/docker-images/ia-service.tar" ]; then
        log "Construindo e exportando IA Service..."
        cd residencia4-ia-main
        docker build -t globo-ia:latest .
        docker save globo-ia:latest -o ../Globo-Front-main/src-tauri/resources/docker-images/ia-service.tar
        cd ..
        log "IA Service exportado ($(du -h Globo-Front-main/src-tauri/resources/docker-images/ia-service.tar | cut -f1))"
    else
        log "IA Service já existe, pulando..."
    fi
fi

# Verificar tamanho total
log "Verificando tamanho total dos recursos..."
TOTAL_SIZE=$(du -sh Globo-Front-main/src-tauri/resources/ | cut -f1)
echo "📦 Tamanho total dos recursos: $TOTAL_SIZE"

# Listar conteúdo
log "Conteúdo do bundle:"
echo "📁 Recursos:"
ls -lh Globo-Front-main/src-tauri/resources/
echo ""
echo "📦 Imagens Docker:"
ls -lh Globo-Front-main/src-tauri/resources/docker-images/

# Verificar integridade
log "Verificando integridade dos arquivos..."
for file in Globo-Front-main/src-tauri/resources/docker-images/*.tar; do
    if [ -f "$file" ]; then
        if tar -tf "$file" > /dev/null 2>&1; then
            echo "✅ $(basename "$file") - OK"
        else
            echo "❌ $(basename "$file") - CORROMPIDO"
        fi
    fi
done

log "Preparação concluída! ✅"
echo ""
echo "🎯 Próximos passos:"
echo "1. cd Globo-Front-main"
echo "2. npm install --legacy-peer-deps"
echo "3. npm run build"
echo "4. cargo tauri build"
echo ""
echo "📋 Arquivos preparados:"
echo "   - docker-compose.yml"
echo "   - .env"  
echo "   - Backend Python completo"
echo "   - Serviço IA completo"
echo "   - Imagens Docker (PostgreSQL, Backend, IA)"
echo ""
echo "⚠️  Importante: Certifique-se de ter pelo menos 8GB de RAM disponível para o build"
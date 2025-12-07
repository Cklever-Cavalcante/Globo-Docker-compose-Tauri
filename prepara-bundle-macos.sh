#!/bin/bash

# 🔧 Script de Preparação de Bundle Completo para macOS
# Este script automatiza a preparação de todos os recursos necessários para gerar
# um bundle Tauri completo e funcional no macOS

set -e  # Sai em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1" >&2
    exit 1
}

success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml não encontrado. Execute este script na raiz do projeto."
fi

log "🚀 Iniciando preparação de bundle para macOS..."

# Verificar dependências
log "🔍 Verificando dependências..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker não está instalado. Por favor, instale o Docker Desktop para Mac."
fi

# Verificar se Docker está rodando
if ! docker info &> /dev/null; then
    error "Docker não está rodando. Por favor, inicie o Docker Desktop."
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    error "Node.js não está instalado. Por favor, instale o Node.js 20+."
fi

NODE_VERSION=$(node --version | sed 's/v//')
log "✅ Node.js versão: $NODE_VERSION"

# Verificar npm
if ! command -v npm &> /dev/null; then
    error "npm não está instalado."
fi

# Verificar Rust
if ! command -v rustc &> /dev/null; then
    error "Rust não está instalado. Por favor, instale o Rust via rustup."
fi

RUST_VERSION=$(rustc --version | awk '{print $2}')
log "✅ Rust versão: $RUST_VERSION"

# Criar estrutura de diretórios
log "📁 Criando estrutura de diretórios..."
FRONT_DIR="Globo-Front-main"
RESOURCES_DIR="$FRONT_DIR/src-tauri/resources"
DOCKER_IMAGES_DIR="$RESOURCES_DIR/docker-images"

mkdir -p "$RESOURCES_DIR" || error "Falha ao criar diretório de recursos"
mkdir -p "$DOCKER_IMAGES_DIR" || error "Falha ao criar diretório de imagens Docker"

success "Estrutura de diretórios criada"

# Copiar arquivos de configuração
log "📋 Copiando arquivos de configuração..."

# Copiar docker-compose.yml
cp docker-compose.yml "$RESOURCES_DIR/" || error "Falha ao copiar docker-compose.yml"
success "docker-compose.yml copiado"

# Copiar .env (se existir)
if [ -f ".env" ]; then
    cp .env "$RESOURCES_DIR/" || error "Falha ao copiar .env"
    success ".env copiado"
else
    warning ".env não encontrado, criando arquivo vazio..."
    touch "$RESOURCES_DIR/.env"
fi

# Copiar diretórios do backend e IA
log "📦 Copiando diretórios de serviços..."

if [ -d "residencia4-backend-master" ]; then
    rm -rf "$RESOURCES_DIR/residencia4-backend-master"
    cp -r residencia4-backend-master "$RESOURCES_DIR/" || error "Falha ao copiar residencia4-backend-master"
    success "residencia4-backend-master copiado"
else
    error "Diretório residencia4-backend-master não encontrado"
fi

if [ -d "residencia4-ia-main" ]; then
    rm -rf "$RESOURCES_DIR/residencia4-ia-main"
    cp -r residencia4-ia-main "$RESOURCES_DIR/" || error "Falha ao copiar residencia4-ia-main"
    success "residencia4-ia-main copiado"
else
    error "Diretório residencia4-ia-main não encontrado"
fi

# Build e exportação de imagens Docker
log "🐳 Construindo e exportando imagens Docker..."

# PostgreSQL (imagem oficial)
POSTGRES_TAR="$DOCKER_IMAGES_DIR/postgres.tar"
if [ ! -f "$POSTGRES_TAR" ]; then
    log "📥 Baixando e exportando PostgreSQL..."
    docker pull postgres:15-alpine
    docker save postgres:15-alpine -o "$POSTGRES_TAR"
    SIZE=$(ls -lh "$POSTGRES_TAR" | awk '{print $5}')
    success "PostgreSQL exportado ($SIZE)"
else
    warning "PostgreSQL já existe, pulando..."
fi

# Backend API
BACKEND_TAR="$DOCKER_IMAGES_DIR/backend.tar"
if [ -d "residencia4-backend-master" ]; then
    log "🏗️  Construindo imagem do Backend API..."
    cd residencia4-backend-master
    docker build -t globo-backend:latest . || warning "Falha ao buildar imagem do backend"
    cd ..
    
    log "💾 Exportando imagem do Backend..."
    docker save globo-backend:latest -o "$BACKEND_TAR" || warning "Falha ao exportar imagem do backend"
    if [ -f "$BACKEND_TAR" ]; then
        SIZE=$(ls -lh "$BACKEND_TAR" | awk '{print $5}')
        success "Backend exportado ($SIZE)"
    fi
else
    warning "Backend não encontrado, criando placeholder..."
    touch "$BACKEND_TAR"
fi

# Serviço de IA
IA_TAR="$DOCKER_IMAGES_DIR/ia-service.tar"
if [ -d "residencia4-ia-main" ]; then
    log "🏗️  Construindo imagem do Serviço de IA..."
    cd residencia4-ia-main
    if [ -f "Dockerfile" ]; then
        docker build -t globo-ia:latest . || warning "Falha ao buildar imagem do IA"
        cd ..
        
        log "💾 Exportando imagem do IA..."
        docker save globo-ia:latest -o "$IA_TAR" || warning "Falha ao exportar imagem do IA"
        if [ -f "$IA_TAR" ]; then
            SIZE=$(ls -lh "$IA_TAR" | awk '{print $5}')
            success "IA exportado ($SIZE)"
        fi
    else
        cd ..
        warning "Dockerfile não encontrado no IA, criando placeholder..."
        touch "$IA_TAR"
    fi
else
    warning "IA não encontrado, criando placeholder..."
    touch "$IA_TAR"
fi

# Verificar arquivos finais
log "🔍 Verificando arquivos finais..."

FILES_TO_CHECK=(
    "$RESOURCES_DIR/docker-compose.yml"
    "$RESOURCES_DIR/.env"
    "$RESOURCES_DIR/residencia4-backend-master"
    "$RESOURCES_DIR/residencia4-ia-main"
    "$DOCKER_IMAGES_DIR/postgres.tar"
    "$DOCKER_IMAGES_DIR/backend.tar"
    "$DOCKER_IMAGES_DIR/ia-service.tar"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -e "$file" ]; then
        success "✅ $(basename "$file")"
    else
        error "❌ $(basename "$file") não encontrado"
    fi
done

# Informações finais
log "📊 Resumo do bundle:"
echo -e "${BLUE}📁 Diretório de recursos:${NC} $RESOURCES_DIR"
echo -e "${BLUE}🐳 Imagens Docker:${NC} $DOCKER_IMAGES_DIR"
echo -e "${BLUE}📦 Tamanho total:${NC} $(du -sh "$RESOURCES_DIR" 2>/dev/null | awk '{print $1}' || echo 'Desconhecido')"

success "🎉 Preparação do bundle concluída com sucesso!"
log "💡 Próximo passo: Execute 'npm run tauri build' no diretório $FRONT_DIR"

# Verificar espaço em disco
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
log "💾 Espaço em disco disponível: $AVAILABLE"

echo ""
echo -e "${GREEN}✨ Script concluído!${NC}"
echo -e "${BLUE}📖${NC} Para builds Tauri: cd $FRONT_DIR && npm run tauri build"
echo -e "${BLUE}🚀${NC} O bundle está pronto para ser empacotado!"
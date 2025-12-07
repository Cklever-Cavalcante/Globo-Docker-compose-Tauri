# 🐧 GUIA COMPLETO: Build de Bundle Completo no Linux Mint

## 📋 Visão Geral

Este guia detalha **todo o processo necessário** para gerar builds de bundles completos no Linux Mint, incluindo:
- Frontend Angular + Tauri
- Backend Python FastAPI 
- Serviço de IA Python
- PostgreSQL via Docker Compose
- Imagens Docker pré-construídas
- Todos os recursos embarcados

## 🏗️ Arquitetura do Bundle Completo

```
Bundle Completo:
├── Frontend (Tauri + Angular)
│   ├── Interface Angular compilada
│   ├── Backend Rust com comandos Docker
│   └── Recursos embarcados:
│       ├── docker-compose.yml
│       ├── .env
│       ├── Backend Python completo
│       ├── Serviço IA completo
│       └── Imagens Docker (.tar)
└── Executáveis:
    ├── .deb (Ubuntu/Debian)
    ├── .AppImage (Universal Linux)
    └── .rpm (RedHat/Fedora)
```

## 🔄 Processo Completo Passo a Passo

### 1. Preparação do Ambiente Linux Mint

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências essenciais
sudo apt install -y \
    curl \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    libgtk-3-dev \
    libwebkit2gtk-4.1-dev \
    libappindicator3-dev \
    librsvg2-dev \
    patchelf \
    librust-openssl-dev

# Instalar Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Instalar Tauri CLI
cargo install tauri-cli

# Verificar instalações
node --version    # v20.x.x
npm --version     # 10.x.x
cargo --version   # 1.7x.x
tauri --version   # 2.x.x
```

### 2. Clonar e Preparar o Projeto

```bash
# Clonar repositório
git clone https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri.git
cd Globo-Docker-compose-Tauri

# Estrutura do projeto
ls -la
# ├── Globo-Front-main/          # Frontend Tauri + Angular
# ├── residencia4-backend-master/ # Backend FastAPI
# ├── residencia4-ia-main/       # Serviço IA
# ├── docker-compose.yml         # Orquestração Docker
# ├── .env                       # Variáveis ambiente
# └── .github/workflows/         # CI/CD
```

### 3. Construir Imagens Docker (PASSO CRÍTICO)

```bash
# Criar diretório para imagens Docker
mkdir -p Globo-Front-main/src-tauri/resources/docker-images

# Build PostgreSQL image (usa imagem oficial)
docker pull postgres:15-alpine
docker save postgres:15-alpine -o Globo-Front-main/src-tauri/resources/docker-images/postgres.tar

# Build Backend API image
cd residencia4-backend-master
docker build -t globo-backend:latest .
docker save globo-backend:latest -o ../Globo-Front-main/src-tauri/resources/docker-images/backend.tar
cd ..

# Build IA Service image  
cd residencia4-ia-main
docker build -t globo-ia:latest .
docker save globo-ia:latest -o ../Globo-Front-main/src-tauri/resources/docker-images/ia-service.tar
cd ..

# Verificar imagens criadas (devem ter > 1GB cada)
ls -lh Globo-Front-main/src-tauri/resources/docker-images/
# postgres.tar    (~200MB)
# backend.tar     (~2-3GB) 
# ia-service.tar  (~3-4GB)
```

### 4. Preparar Recursos para o Bundle

```bash
# Copiar arquivos essenciais para o bundle
cp docker-compose.yml Globo-Front-main/src-tauri/resources/
cp .env Globo-Front-main/src-tauri/resources/

# Copiar backend completo
cp -r residencia4-backend-master Globo-Front-main/src-tauri/resources/

# Copiar serviço IA completo  
cp -r residencia4-ia-main Globo-Front-main/src-tauri/resources/

# Verificar estrutura de recursos
tree Globo-Front-main/src-tauri/resources/ -L 2
```

### 5. Configurar Tauri para Bundle Completo

```bash
# Verificar configuração do bundle
cat Globo-Front-main/src-tauri/tauri.conf.json | grep -A 20 '"bundle"'

# A configuração deve incluir:
# - "resources": todos os arquivos copiados
# - "targets": "all" (para todos os formatos)
# - "active": true
```

### 6. Instalar Dependências do Frontend

```bash
cd Globo-Front-main

# Limpar cache se necessário
rm -rf node_modules package-lock.json

# Instalar dependências com legacy peer deps
npm install --legacy-peer-deps

# Verificar dependências críticas
npm list @tauri-apps/api
npm list @tauri-apps/cli
```

### 7. Build Frontend Angular

```bash
# Build otimizado para produção
npm run build

# Verificar build
ls -la dist/globo-monitor-front/
# Deve conter:
# - index.html
# - main-*.js (principal)
# - styles-*.css
# - assets/
# - favicon.ico
```

### 8. Build Tauri Completo

```bash
# Build Tauri com todos os recursos
cargo tauri build

# OU usando npm script (se disponível)
npm run tauri build
```

### 9. Monitorar o Processo de Build

O build Tauri vai:
1. **Compilar Rust** (~5-10 minutos)
2. **Empacotar recursos** (~2-3 minutos) 
3. **Criar instaladores** (~3-5 minutos)
4. **Total**: ~15-20 minutos

```bash
# Acompanhar progresso
tail -f /tmp/tauri-build.log &

# Verificar uso de recursos
htop
```

### 10. Verificar Builds Gerados

```bash
# Listar todos os formatos gerados
ls -la src-tauri/target/release/bundle/

# Debian/Ubuntu
ls -lh src-tauri/target/release/bundle/deb/*.deb

# AppImage (universal)
ls -lh src-tauri/target/release/bundle/appimage/*.AppImage

# RPM (RedHat/Fedora)
ls -lh src-tauri/target/release/bundle/rpm/*.rpm

# Executável principal
ls -lh src-tauri/target/release/app
```

## 📦 Tamanhos Esperados dos Bundles

| Formato | Tamanho | Conteúdo |
|---------|---------|----------|
| `.deb` | 400-600MB | Frontend + Backend + Docker + IA |
| `.AppImage` | 450-650MB | Bundle universal completo |
| `.rpm` | 400-600MB | Pacote RedHat completo |
| Executável | 150-200MB | Apenas app Tauri |

## 🔧 Solução de Problemas Comuns

### 1. Erro: "libwebkit2gtk-4.1-dev not found"
```bash
# Linux Mint 21+ (Ubuntu 22.04 base)
sudo apt install libwebkit2gtk-4.1-dev

# Linux Mint 20 (Ubuntu 20.04 base)  
sudo apt install libwebkit2gtk-4.0-dev
# E atualizar tauri.conf.json para usar 4.0
```

### 2. Erro: "docker: command not found"
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Erro: "memory allocation failed" (falta RAM)
```bash
# Criar swap temporária
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Monitorar uso
free -h
```

### 4. Erro: "disk space full"
```bash
# Verificar espaço
df -h

# Limpar Docker
docker system prune -a

# Build incremental
cargo tauri build --verbose
```

### 5. Build muito lento
```bash
# Usar todos os cores CPU
cargo tauri build --config '{"build": {"beforeBuildCommand": "npm run build"}}'

# Paralelizar Rust
export MAKEFLAGS=-j$(nproc)
```

## 🚀 Testando o Bundle Gerado

### Testar AppImage (Universal)
```bash
# Tornar executável
chmod +x src-tauri/target/release/bundle/appimage/*.AppImage

# Executar
./src-tauri/target/release/bundle/appimage/globo-monitor_*.AppImage

# Verificar logs
~/.local/share/globo-monitor/logs/
```

### Testar DEB (Ubuntu/Debian)
```bash
# Instalar
sudo dpkg -i src-tauri/target/release/bundle/deb/*.deb

# Resolver dependências se necessário
sudo apt --fix-broken install

# Executar
globo-monitor
# ou
/usr/bin/globo-monitor
```

### Verificar integração Docker
```bash
# App deve iniciar containers automaticamente
docker ps

# Verificar logs dos containers
docker logs globo-postgres
docker logs globo-backend  
docker logs globo-ia
```

## 📊 Otimizações para Builds Futuros

### 1. Cache de Builds
```bash
# Manter cache Cargo
cache: ~/.cargo/registry

# Cache npm
cache: ~/.npm

# Cache Docker
docker build --cache-from globo-backend:latest
```

### 2. Build Parcial (apenas mudanças)
```bash
# Build apenas frontend
npm run build

# Build apenas Rust (rápido)
cargo build --release

# Reempacotar
cargo tauri build --skip-build
```

### 3. Comprimir Imagens Docker
```bash
# Usar Alpine quando possível
FROM python:3.10-alpine

# Multi-stage builds
# Build em imagem grande, runtime em imagem pequena

# Comprimir ao salvar
docker save myapp:latest | gzip > myapp.tar.gz
```

## 🎯 Checklist Final de Validação

- [ ] Frontend Angular buildado sem erros
- [ ] Imagens Docker criadas e salvas (.tar)
- [ ] Recursos copiados para src-tauri/resources/
- [ ] Tauri configurado com todos os recursos
- [ ] Build completo gerado sem erros
- [ ] Pelo menos 1 instalador funcional (.deb/.AppImage)
- [ ] Aplicação inicia containers Docker ao executar
- [ ] Interface web acessível via Tauri
- [ ] Backend API respondendo na porta 8000
- [ ] Serviço IA funcionando na porta 8001

## 📝 Notas Importantes

1. **Tamanho é normal**: Bundles completos são grandes (400-600MB) pois incluem:
   - Runtime Python completo (IA)
   - Modelos ML/AI (YOLO, MobileNet, etc)
   - Imagens Docker com todas dependências
   - PostgreSQL embutido

2. **Primeira execução**: Pode demorar 1-2 minutos para extrair e iniciar containers

3. **Docker necessário**: Usuário final precisa ter Docker/Podman instalado

4. **Recursos**: Mínimo 4GB RAM, 8GB recomendado para IA

---

**Build completo gerado!** 🎉 
A aplicação está 100% funcional com todos os serviços integrados.
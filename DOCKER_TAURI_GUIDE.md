# Guia Completo de Instalação e Execução - Globo Monitor

Este guia apresenta **duas formas** de executar o Globo Monitor:

1. **[Modo Tradicional](#modo-1-tradicional---execução-via-código-fonte)**: Execução direta do código fonte (recomendado para desenvolvimento)
2. **[Modo Experimental](#modo-2-experimental---docker--tauri-desktop-app)**: Aplicação desktop com Docker (em fase de testes, ideal para usuários finais)

---

## Repositórios do Projeto

O Globo Monitor está organizado em **dois formatos diferentes** de repositórios, cada um adequado para um método de execução:

### Modo Tradicional - Repositórios Separados

Para o **modo tradicional** (execução via código fonte), o projeto está dividido em **3 repositórios independentes**:

| Componente | Repositório | Descrição |
|------------|-------------|-----------|
| **Backend** | [github.com/wilkenio/residencia4-backend](https://github.com/wilkenio/residencia4-backend) | API FastAPI, gerenciamento de vídeos e banco de dados |
| **IA Service** | [github.com/wilkenio/residencia4-ia](https://github.com/wilkenio/residencia4-ia) | Serviço de análise de vídeo com ML/AI |
| **Frontend** | [github.com/dsilvand/Globo-Front](https://github.com/dsilvand/Globo-Front) | Interface Angular do usuário |

> **Nota**: Você precisará clonar os **3 repositórios separadamente** e configurar cada um individualmente seguindo as instruções do [Modo Tradicional](#modo-1-tradicional---execução-via-código-fonte).

### Modo Experimental - Repositório Unificado

Para o **modo experimental** (Docker + Tauri), existe um **repositório único** que contém:

- ✅ Todos os 3 componentes integrados (Backend, IA, Frontend)
- ✅ Configuração Docker Compose completa
- ✅ Aplicação desktop Tauri
- ✅ **Instaladores pré-compilados** para download direto

| Repositório Unificado | Link |
|----------------------|------|
| **Globo-Docker-compose-Tauri** | [github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri](https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri) |

**Onde encontrar os instaladores:**
- Acesse a seção [**Releases**](https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri/releases) do repositório
- Baixe o instalador apropriado para seu sistema operacional (Windows, macOS ou Linux)
- Não é necessário clonar o repositório se você apenas quer usar os instaladores prontos

---

## Modo 1: Tradicional - Execução via Código Fonte

> **Recomendado para**: Desenvolvedores, contribuidores, debugging e desenvolvimento de novas funcionalidades.

Este método executa cada componente (Backend, IA, Frontend) diretamente no seu ambiente local, oferecendo máxima flexibilidade para desenvolvimento.

### Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Frontend       │────▶│  Backend API    │────▶│  IA Service     │
│  Angular :4200  │     │  FastAPI :8000  │     │  FastAPI :8001  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  PostgreSQL     │
                        │  :5432          │
                        └─────────────────┘
```

---

### Pré-requisitos Globais

Antes de começar, instale os seguintes componentes no seu sistema:

#### 1. Python 3.10+

**Linux (Ubuntu/Debian/Mint):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version  # Verificar versão
```

**macOS:**
```bash
# Usando Homebrew
brew install python@3.10

# Verificar versão
python3 --version
```

**Windows:**
1. Baixe o instalador em [python.org](https://www.python.org/downloads/)
2. Execute o instalador
3. ✅ **IMPORTANTE**: Marque "Add Python to PATH"
4. Verifique no PowerShell:
   ```powershell
   python --version
   ```

#### 2. Node.js 20+

**Linux (Ubuntu/Debian/Mint):**
```bash
# Instalar via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar versão
node --version
npm --version
```

**macOS:**
```bash
# Usando Homebrew
brew install node@20

# Verificar versão
node --version
npm --version
```

**Windows:**
1. Baixe o instalador em [nodejs.org](https://nodejs.org/)
2. Execute o instalador (escolha a versão LTS)
3. Verifique no PowerShell:
   ```powershell
   node --version
   npm --version
   ```

#### 3. PostgreSQL 15+

**Linux (Ubuntu/Debian/Mint):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

# Iniciar serviço
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verificar status
sudo systemctl status postgresql
```

**macOS:**
```bash
# Usando Homebrew
brew install postgresql@15

# Iniciar serviço
brew services start postgresql@15
```

**Windows:**
1. Baixe o instalador em [postgresql.org](https://www.postgresql.org/download/windows/)
2. Execute o instalador
3. Anote a senha do usuário `postgres`
4. O serviço inicia automaticamente

**Configurar Banco de Dados:**
```bash
# Linux/macOS
sudo -u postgres psql

# Windows (no PowerShell como Administrador)
psql -U postgres
```

Dentro do PostgreSQL:
```sql
CREATE DATABASE globo_monitoramento;
CREATE USER globo_user WITH PASSWORD 'root';
GRANT ALL PRIVILEGES ON DATABASE globo_monitoramento TO globo_user;
\q
```

#### 4. FFmpeg (Essencial para processamento de vídeo)

**Linux (Ubuntu/Debian/Mint):**
```bash
sudo apt update
sudo apt install ffmpeg

# Verificar instalação
ffmpeg -version
```

**macOS:**
```bash
brew install ffmpeg

# Verificar instalação
ffmpeg -version
```

**Windows:**
1. Baixe em [ffmpeg.org](https://ffmpeg.org/download.html#build-windows)
2. Extraia para `C:\ffmpeg`
3. Adicione `C:\ffmpeg\bin` ao PATH do sistema:
   - Painel de Controle → Sistema → Configurações Avançadas → Variáveis de Ambiente
   - Edite a variável `Path` e adicione `C:\ffmpeg\bin`
4. Reinicie o terminal e verifique:
   ```powershell
   ffmpeg -version
   ```

---

### Passo 1: Clonar os Repositórios

Como o projeto está dividido em 3 repositórios separados, você precisará clonar cada um:

```bash
# Criar diretório para o projeto
mkdir globo-monitor
cd globo-monitor

# Clonar Backend
git clone https://github.com/wilkenio/residencia4-backend.git

# Clonar IA Service
git clone https://github.com/wilkenio/residencia4-ia.git

# Clonar Frontend
git clone https://github.com/dsilvand/Globo-Front.git
```

Sua estrutura de pastas ficará assim:
```
globo-monitor/
├── residencia4-backend/
├── residencia4-ia/
└── Globo-Front/
```

---

### Passo 2: Configurar o Serviço de IA

#### Linux/macOS:
```bash
# Navegar até a pasta da IA
cd residencia4-ia

# Criar ambiente virtual
python3 -m venv venv_ia

# Ativar ambiente virtual
source venv_ia/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### Windows (PowerShell):
```powershell
# Navegar até a pasta da IA
cd residencia4-ia

# Criar ambiente virtual
python -m venv venv_ia

# Ativar ambiente virtual
.\venv_ia\Scripts\Activate.ps1

# Se houver erro de execução de scripts, execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar dependências
pip install -r requirements.txt
```

> **Nota**: A instalação das dependências de IA pode levar vários minutos devido ao tamanho dos pacotes (PyTorch, TensorFlow, etc.).

---

### Passo 3: Configurar o Backend

**Abra um NOVO terminal** (mantenha o anterior aberto).

#### Linux/macOS:
```bash
# Navegar até a pasta do backend
cd residencia4-backend

# Criar ambiente virtual
python3 -m venv venv_backend

# Ativar ambiente virtual
source venv_backend/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### Windows (PowerShell):
```powershell
# Navegar até a pasta do backend
cd residencia4-backend

# Criar ambiente virtual
python -m venv venv_backend

# Ativar ambiente virtual
.\venv_backend\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

---

### Passo 4: Configurar o Frontend

**Abra um TERCEIRO terminal** (mantenha os anteriores abertos).

#### Linux/macOS/Windows:
```bash
# Navegar até a pasta do frontend
cd Globo-Front

# Instalar dependências
npm install --legacy-peer-deps
```

> **Nota**: O flag `--legacy-peer-deps` é necessário devido a algumas dependências do Angular.

---

### Passo 5: Executar a Aplicação

Agora você deve ter **3 terminais abertos**. Execute os comandos na ordem:

#### Terminal 1: Serviço de IA

**Linux/macOS:**
```bash
cd residencia4-ia
source venv_ia/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Windows:**
```powershell
cd residencia4-ia
.\venv_ia\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

✅ **Aguarde a mensagem**: `Application startup complete.`

#### Terminal 2: Backend API

**Linux/macOS:**
```bash
cd residencia4-backend
source venv_backend/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Windows:**
```powershell
cd residencia4-backend
.\venv_backend\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

✅ **Aguarde a mensagem**: `Application startup complete.`

#### Terminal 3: Frontend Angular

**Linux/macOS/Windows:**
```bash
cd Globo-Front
ng serve --open
```

✅ **Aguarde**: O navegador abrirá automaticamente em `http://localhost:4200`

---

### Verificar Funcionamento

Após iniciar todos os serviços, verifique:

- **Frontend**: http://localhost:4200 (Interface do usuário)
- **Backend API Docs**: http://localhost:8000/docs (Documentação Swagger)
- **IA Service Docs**: http://localhost:8001/docs (Documentação Swagger)

---

### Parar a Aplicação

Para parar os serviços:

1. Em cada terminal, pressione `Ctrl + C`
2. Desative os ambientes virtuais (opcional):
   ```bash
   deactivate
   ```

---

### Troubleshooting - Modo Tradicional

#### Erro: Porta já em uso

**Problema**: `Address already in use`

**Solução**:
```bash
# Linux/macOS - Encontrar processo usando a porta
sudo lsof -i :8000  # ou :8001, :4200
kill -9 <PID>

# Windows - Encontrar e matar processo
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### Erro: Módulo não encontrado

**Problema**: `ModuleNotFoundError`

**Solução**:
```bash
# Certifique-se de que o ambiente virtual está ativado
# E reinstale as dependências
pip install -r requirements.txt
```

#### Erro: FFmpeg não encontrado

**Problema**: `ffmpeg: command not found`

**Solução**: Reinstale o FFmpeg seguindo as instruções de pré-requisitos.

#### Erro: Conexão com PostgreSQL falha

**Problema**: `could not connect to server`

**Solução**:
```bash
# Verificar se o PostgreSQL está rodando
# Linux
sudo systemctl status postgresql

# macOS
brew services list

# Windows
# Verificar em Services (services.msc)
```

---

## Modo 2: Experimental - Docker + Tauri Desktop App

> **⚠️ EXPERIMENTAL**: Este método está em **fase de testes** e serve como um **bônus adicional** ao método tradicional. O objetivo é facilitar a distribuição e execução da aplicação através de instaladores prontos, sem necessidade de configurar manualmente cada componente.

### Vantagens do Modo Experimental

- ✅ **Instalação Simples**: Um único instalador para todo o sistema
- ✅ **Sem Configuração Manual**: Não precisa instalar Python, Node, PostgreSQL separadamente
- ✅ **Isolamento**: Serviços rodando em containers Docker
- ✅ **Portabilidade**: Funciona em Windows, macOS e Linux
- ✅ **Gerenciamento Integrado**: Interface desktop gerencia os containers automaticamente

### Desvantagens

- ⚠️ **Menos Flexível**: Não ideal para desenvolvimento
- ⚠️ **Debugging Complexo**: Mais difícil debugar problemas
- ⚠️ **Overhead**: Pequeno overhead do Docker
- ⚠️ **Em Testes**: Pode conter bugs não descobertos

---

### Arquitetura

```
┌─────────────────────────────────────────┐
│   Globo Monitor Desktop App (Tauri)    │
│   ┌─────────────────────────────────┐   │
│   │   Angular Frontend              │   │
│   │   (Interface do Usuário)        │   │
│   └─────────────────────────────────┘   │
│   ┌─────────────────────────────────┐   │
│   │   Rust Backend                  │   │
│   │   (Gerenciamento Docker)        │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                    ↓
        Comandos Docker/Podman
                    ↓
┌─────────────────────────────────────────┐
│       Docker Compose Services           │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │PostgreSQL│ │ Backend  │ │IA Service│ │
│  │  :5432   │ │  :8000   │ │  :8001   │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
```

---

### Pré-requisito: Docker

A aplicação desktop requer Docker ou Podman para executar os serviços backend.

#### Instalar Docker

**Windows:**
1. Baixe [Docker Desktop para Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Execute o instalador
3. Reinicie o computador se solicitado
4. Abra o Docker Desktop e aguarde inicializar
5. Verifique no PowerShell:
   ```powershell
   docker --version
   docker-compose --version
   ```

**macOS:**
1. Baixe [Docker Desktop para Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Arraste para a pasta Applications
3. Abra o Docker Desktop
4. Aguarde o ícone da baleia ficar estável na barra superior
5. Verifique no Terminal:
   ```bash
   docker --version
   docker-compose --version
   ```

**Linux (Ubuntu/Debian/Mint):**
```bash
# Instalar Docker
sudo apt update
sudo apt install docker.io docker-compose

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Relogar ou executar
newgrp docker

# Verificar instalação
docker --version
docker-compose --version
```

**Linux (Podman - Alternativa):**
```bash
# Ubuntu/Debian
sudo apt install podman podman-compose

# Fedora
sudo dnf install podman podman-compose

# Verificar
podman --version
podman-compose --version
```

---

### Opção A: Instaladores Pré-compilados (Recomendado)

Este é o método mais simples para usuários finais.

#### Passo 1: Baixar o Instalador

Acesse a página de [Releases](https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri/releases) no GitHub e baixe o instalador apropriado:

**Windows:**
- `globo-monitor_X.X.X_x64_en-US.msi` (Instalador MSI - Recomendado)
- `globo-monitor_X.X.X_x64-setup.exe` (Instalador NSIS - Alternativo)

**macOS:**
- `globo-monitor_X.X.X_universal.dmg` (Suporta Intel e Apple Silicon)

**Linux:**
- `globo-monitor_X.X.X_amd64.deb` (Debian/Ubuntu/Mint)
- `globo-monitor-X.X.X-1.x86_64.rpm` (Fedora/RHEL)
- `globo-monitor_X.X.X_amd64.AppImage` (Universal)

#### Passo 2: Instalar

**Windows:**
```powershell
# Duplo clique no instalador MSI ou EXE
# OU via linha de comando:
msiexec /i globo-monitor_X.X.X_x64_en-US.msi
```

**macOS:**
1. Duplo clique no arquivo `.dmg`
2. Arraste o ícone "Globo Monitor" para a pasta "Applications"
3. **Primeira execução**:
   - Abra "System Preferences" → "Security & Privacy"
   - Clique em "Open Anyway" para permitir a execução

**Linux (Debian/Ubuntu/Mint):**
```bash
sudo dpkg -i globo-monitor_X.X.X_amd64.deb

# Se houver dependências faltando:
sudo apt-get install -f
```

**Linux (Fedora/RHEL):**
```bash
sudo rpm -i globo-monitor-X.X.X-1.x86_64.rpm
```

**Linux (AppImage):**
```bash
chmod +x globo-monitor_X.X.X_amd64.AppImage
./globo-monitor_X.X.X_amd64.AppImage
```

#### Passo 3: Executar

Após a instalação:

- **Windows**: Menu Iniciar → Globo Monitor
- **macOS**: Applications → Globo Monitor
- **Linux**: Menu de aplicações ou execute `globo-monitor` no terminal

#### Passo 4: Gerenciar Serviços

A aplicação desktop possui controles integrados:

1. **Iniciar Serviços**: Clique no botão "Start Services"
   - Inicia PostgreSQL, Backend e IA Service automaticamente
   - Na primeira execução, o download das imagens Docker pode levar alguns minutos

2. **Parar Serviços**: Clique no botão "Stop Services"
   - Para todos os containers

3. **Verificar Status**: Clique em "Check Status"
   - Mostra o status de cada serviço

---

### Opção B: Compilação Local (Para Desenvolvedores)

Se você deseja compilar a aplicação desktop localmente:

#### Pré-requisitos Adicionais

1. **Rust 1.91+**
   ```bash
   # Linux/macOS
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   
   # Windows
   # Baixe e instale: https://rustup.rs/
   
   # Verificar
   rustc --version
   cargo --version
   ```

2. **Dependências de Sistema**

   **Linux (Ubuntu/Debian/Mint):**
   ```bash
   sudo apt install libwebkit2gtk-4.1-dev \
     build-essential \
     curl \
     wget \
     file \
     libssl-dev \
     libgtk-3-dev \
     libayatana-appindicator3-dev \
     librsvg2-dev
   ```

   **macOS:**
   ```bash
   xcode-select --install
   ```

   **Windows:**
   - Instale [Microsoft Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Instale [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

#### Passos de Compilação

```bash
# 1. Clonar repositório
git clone https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri.git
cd Globo-Docker-compose-Tauri

# 2. Instalar dependências do frontend
cd Globo-Front-main
npm install --legacy-peer-deps

# 3. Compilar aplicação Tauri
npx tauri build
```

Os instaladores estarão em:
- **Linux**: `src-tauri/target/release/bundle/deb/`, `src-tauri/target/release/bundle/rpm/`
- **Windows**: `src-tauri/target/release/bundle/msi/`, `src-tauri/target/release/bundle/nsis/`
- **macOS**: `src-tauri/target/release/bundle/dmg/`

---

### Troubleshooting - Modo Experimental

#### Docker não está rodando

**Sintoma**: Erro ao iniciar serviços

**Solução**:
- **Windows/macOS**: Abra o Docker Desktop e aguarde inicializar
- **Linux**: `sudo systemctl start docker`

#### Porta 5432 já em uso

**Sintoma**: PostgreSQL container falha ao iniciar

**Solução**: Pare o PostgreSQL local
```bash
# Linux
sudo systemctl stop postgresql

# macOS
brew services stop postgresql

# Windows
# Parar serviço PostgreSQL via Services (services.msc)
```

#### Aplicação não conecta ao backend

**Verificar se containers estão rodando**:
```bash
docker-compose ps
# OU
podman-compose ps
```

**Verificar logs**:
```bash
docker-compose logs backend
docker-compose logs ia-service
```

---

## Comparação: Modo Tradicional vs Experimental

| Aspecto                | Modo Tradicional                        | Modo Experimental                     |
|------------------------|-----------------------------------------|---------------------------------------|
| **Instalação**         | Manual (Python, Node, PostgreSQL, etc.) | Instalador único                      |
| **Configuração**       | Complexa (3 ambientes virtuais)         | Automática                            |
| **Portabilidade**      | Média (depende do ambiente)             | Alta (funciona em qualquer OS)        |
| **Desenvolvimento**    | ✅ Ideal                                | ❌ Menos flexível                     |
| **Debugging**          | ✅ Fácil                                | ❌ Mais complexo                      |
| **Distribuição**       | ❌ Difícil para usuários finais         | ✅ Ideal para usuários finais         |
| **Isolamento**         | Baixo                                   | Alto (containers)                     |
| **Performance**        | Nativa                                  | Overhead mínimo do Docker             |
| **Atualizações**       | `git pull` + reinstalar deps            | Baixar novo instalador                |
| **Status**             | ✅ Estável                              | ⚠️ Experimental                       |

---

## Recomendações de Uso

### Use o Modo Tradicional quando:
- ✅ Você é desenvolvedor ou contribuidor
- ✅ Precisa debugar problemas
- ✅ Quer desenvolver novas funcionalidades
- ✅ Precisa fazer testes rápidos
- ✅ Quer entender o funcionamento interno

### Use o Modo Experimental quando:
- ✅ Você é usuário final
- ✅ Quer apenas usar a aplicação
- ✅ Não quer configurar manualmente
- ✅ Precisa de isolamento entre ambientes
- ✅ Quer facilitar a distribuição

---

## Recursos Adicionais

- [Documentação Tauri](https://tauri.app/v1/guides/)
- [Documentação Docker Compose](https://docs.docker.com/compose/)
- [Guia de Release](Globo-Front-main/RELEASE.md)
- [GitHub Actions Workflow](.github/workflows/README.md)
- [Walkthrough Completo](docs/walkthrough.md)

## Suporte

Para problemas ou dúvidas:

1. Verifique a seção de Troubleshooting apropriada
2. Consulte os logs dos serviços
3. Abra uma [issue no GitHub](https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri/issues)

---

**Desenvolvido com ❤️ usando [Angular](https://angular.io), [FastAPI](https://fastapi.tiangolo.com), [Tauri](https://tauri.app) e [Docker](https://docker.com)**

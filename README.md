# 🎥 Globo Monitor

> **Sistema Inteligente de Monitoramento de Qualidade de Vídeo para Transmissões Ao Vivo**

[![Tauri](https://img.shields.io/badge/Tauri-2.0-blue)](https://tauri.app)
[![Angular](https://img.shields.io/badge/Angular-20.0-red)](https://angular.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.10-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🚀 **O que é o Globo Monitor?**

O **Globo Monitor** é uma solução completa e inteligente para monitoramento em tempo real da qualidade de transmissões de vídeo. Desenvolvido com tecnologia de ponta, o sistema detecta automaticamente anomalias como problemas de inteligibilidade, des sincronização de áudio/vídeo (lipsync) e outros problemas que podem comprometer a experiência do telespectador.

### ✨ **Principais Recursos**

- 🔍 **Monitoramento Inteligente 24/7** com IA avançada
- ⚡ **Detecção em Tempo Real** de anomalias de transmissão
- 🖥️ **Interface Desktop Multiplataforma** (Windows, macOS, Linux)
- 📊 **Dashboard Interativo** com métricas e estatísticas
- 🔔 **Sistema de Notificações** instantâneas via desktop
- 📈 **Relatórios Detalhados** de qualidade da transmissão
- 🐳 **Arquitetura Containerizada** para fácil deploy

## 🏗️ **Arquitetura do Sistema**

```
┌─────────────────────────────────────────────────────────────┐
│              🖥️  Aplicação Desktop (Tauri + Angular)       │
│              Interface intuitiva e responsiva              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  🐳 Docker Compose                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ 🗄️ PostgreSQL│  │ 🚀 Backend  │  │ 🤖 IA        │       │
│  │   (5432)    │  │ API (8000)  │  │ Service     │       │
│  │             │  │ FastAPI     │  │ (8001)      │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 **Inteligência Artificial**

Nossa IA utiliza modelos de ponta:
- **YOLOv8** - Detecção de objetos e padrões
- **MobileNetV2** - Classificação de imagens
- **SyncNet** - Sincronização áudio/vídeo
- **Wav2Vec2** - Processamento de áudio

## 📥 **Download e Instalação**

### 🎯 **Para Usuários Finais**

#### **Windows** 📎
- **Instalador MSI** (Recomendado): [globo-monitor_0.1.0_x64_en-US.msi](Globo-Front-main/src-tauri/target/release/bundle/msi/globo-monitor_0.1.0_x64_en-US.msi)
- **Instalador EXE**: [globo-monitor_0.1.0_x64-setup.exe](Globo-Front-main/src-tauri/target/release/bundle/nsis/globo-monitor_0.1.0_x64-setup.exe)

#### **macOS** 🍎
- **DMG Universal**: Em breve disponível

#### **Linux** 🐧
- **AppImage**: [globo-monitor_0.1.0_amd64.AppImage](github_actions/appimage/globo-monitor_0.1.0_amd64.AppImage)
- **DEB Package**: [globo-monitor_0.1.0_amd64.deb](github_actions/deb/globo-monitor_0.1.0_amd64.deb)
- **RPM Package**: [globo-monitor-0.1.0-1.x86_64.rpm](github_actions/rpm/globo-monitor-0.1.0-1.x86_64.rpm)

### ⚙️ **Pré-requisitos do Sistema**

- **Windows**: Windows 10/11 (64-bit)
- **macOS**: macOS 10.15+ (Intel/Apple Silicon)
- **Linux**: Ubuntu 18.04+, Fedora 30+, Debian 10+
- **Docker**: Docker Desktop ou Podman (instalado automaticamente)

## 🚀 **Começando Agora Mesmo**

### 1️⃣ **Download e Instalação**

**Windows:**
```bash
# Baixe o instalador MSI
# Execute como Administrador
# Siga o assistente de instalação
```

**Linux:**
```bash
# AppImage (Recomendado)
chmod +x globo-monitor_0.1.0_amd64.AppImage
./globo-monitor_0.1.0_amd64.AppImage

# Ou instale o pacote DEB
sudo dpkg -i globo-monitor_0.1.0_amd64.deb
```

### 2️⃣ **Primeira Execução**

1. **Execute o aplicativo** (ele iniciará automaticamente)
2. **O sistema detectará** se o Docker está instalado
3. **Se necessário**, o Docker será instalado automaticamente
4. **Os containers serão iniciados** em background
5. **Pronto!** O dashboard será exibido automaticamente

### 3️⃣ **Verificação Rápida**

Abra seu navegador e acesse:
- **Dashboard**: http://localhost:4200
- **API Backend**: http://localhost:8000/docs
- **IA Service**: http://localhost:8001/

## 🛠️ **Desenvolvimento**

### 📋 **Pré-requisitos para Desenvolvedores**

- **Node.js** 20+ 
- **Rust** 1.91+
- **Python** 3.10+
- **Docker** ou **Podman**

### 🏃‍♂️ **Desenvolvimento Local**

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/globo-monitor.git
cd globo-monitor

# Inicie os serviços Docker
docker-compose up -d

# Frontend (em outro terminal)
cd Globo-Front-main
npm install --legacy-peer-deps
npm run tauri dev

# Backend API (em outro terminal)
cd residencia4-backend-master
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# IA Service (em outro terminal)
cd residencia4-ia-main
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 🔧 **Build e Distribuição**

### 🏗️ **Build Local**

```bash
cd Globo-Front-main
npm install --legacy-peer-deps
npm run build
npm run tauri build
```

### 🌐 **Build com GitHub Actions**

Os builds automáticos são gerados via GitHub Actions para:
- ✅ Windows (.exe, .msi)
- ✅ macOS (.dmg Universal)
- ✅ Linux (.deb, .rpm, .AppImage)

**Acesse**: [Releases](../../releases) para baixar as versões mais recentes.

## 📚 **Documentação**

- 📖 **[Guia Completo](docs/walkthrough.md)** - Processo completo de dockerização
- 🔧 **[Guia de Release](Globo-Front-main/RELEASE.md)** - Como criar novos releases
- 🔄 **[CI/CD Pipeline](Globo-Front-main/.github/workflows/README.md)** - Configuração do GitHub Actions

## 🐛 **Solução de Problemas**

### **Docker não inicia?**
```bash
# Verifique se o Docker está rodando
docker --version

# Reinicie os serviços
docker-compose down
docker-compose up -d
```

### **Aplicação não conecta?**
```bash
# Verifique as portas
netstat -an | findstr "8000"
netstat -an | findstr "8001"
netstat -an | findstr "5432"
```

### **Erro de permissão no Linux?**
```bash
# Adicione seu usuário ao grupo docker
sudo usermod -aG docker $USER
# Faça logout e login novamente
```

## 🤝 **Contribuindo**

Contribuições são bem-vindas! Para começar:

1. **Fork** o projeto
2. **Crie uma branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra um Pull Request**

## 📞 **Suporte**

- 📧 **Email**: suporte@globomonitor.com
- 💬 **Discord**: [Entre no nosso servidor](https://discord.gg/globomonitor)
- 📚 **Wiki**: [Documentação técnica](https://github.com/seu-usuario/globo-monitor/wiki)

## 📝 **Licença**

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 **Agradecimentos**

- **[Tauri](https://tauri.app)** - Framework desktop incrível
- **[Angular](https://angular.io)** - Framework web robusto
- **[Docker](https://docker.com)** - Containerização perfeita
- **[Globo](https://globo.com)** - Pela oportunidade de desenvolver esta solução

---

<div align="center">
  <strong>Desenvolvido com ❤️ pela equipe de Engenharia de Qualidade</strong><br>
  <em>Transformando o monitoramento de vídeo com inteligência artificial</em>
</div>
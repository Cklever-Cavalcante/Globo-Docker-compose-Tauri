# Globo Monitor - Docker Compose + Tauri

Aplicação desktop de monitoramento com análise de vídeo por IA, dockerizada com Podman/Docker e empacotada com Tauri.

## 🏗️ Arquitetura

```
Globo Monitor Desktop App (Tauri + Angular)
    ↓
Docker Compose Services:
    ├── PostgreSQL (Database)
    ├── Backend API (FastAPI)
    └── IA Service (ML/AI Analysis)
```

## 📦 Estrutura do Projeto

```
.
├── Globo-Front-main/          # Frontend Angular + Tauri
│   ├── src-tauri/             # Backend Rust (Docker commands)
│   └── .github/workflows/     # CI/CD para builds multiplataforma
├── residencia4-backend-master/ # Backend FastAPI
├── residencia4-ia-main/       # Serviço de IA
├── docker-compose.yml         # Orquestração dos serviços
├── .env                       # Variáveis de ambiente
└── scripts/                   # Scripts auxiliares
```

## 🚀 Quick Start

### Pré-requisitos
- Docker ou Podman
- Node.js 20+
- Rust 1.91+ (para desenvolvimento)

### Desenvolvimento

```bash
# 1. Iniciar serviços Docker
docker-compose up -d
# ou
podman-compose up -d

# 2. Iniciar aplicação Tauri
cd Globo-Front-main
npm install --legacy-peer-deps
npx tauri dev
```

### Produção (Build Local)

```bash
cd Globo-Front-main
npm install --legacy-peer-deps
npx tauri build
```

Os instaladores estarão em `Globo-Front-main/src-tauri/target/release/bundle/`

## 📥 Downloads

Os instaladores para todas as plataformas são gerados automaticamente via GitHub Actions:

- **Windows**: `.exe`, `.msi`
- **macOS**: `.dmg` (Universal)
- **Linux**: `.deb`, `.rpm`, `.AppImage`

Veja a seção [Releases](../../releases) para baixar a versão mais recente.

## 📚 Documentação

- [Walkthrough Completo](docs/walkthrough.md) - Processo de dockerização e integração Tauri
- [Guia de Release](Globo-Front-main/RELEASE.md) - Como criar releases
- [GitHub Actions](Globo-Front-main/.github/workflows/README.md) - CI/CD

## 🐳 Serviços Docker

### PostgreSQL
- **Porta**: 5432
- **Database**: globo_monitoramento
- **Volume**: `globo_docker_postgres_data`

### Backend API
- **Porta**: 8000
- **Framework**: FastAPI + SQLAlchemy
- **Volumes**: videos, thumbnails, HLS output

### IA Service
- **Porta**: 8001
- **Modelos**: YOLOv8, MobileNetV2, SyncNet, Wav2Vec2
- **Volume**: temp videos

## 🛠️ Tecnologias

- **Frontend**: Angular 20 + Tauri 2
- **Backend**: Python 3.10 + FastAPI
- **IA**: PyTorch, TensorFlow, Ultralytics YOLO
- **Database**: PostgreSQL 15
- **Containerização**: Docker/Podman
- **CI/CD**: GitHub Actions

## 📝 Licença

[Adicionar licença]

## 👥 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

**Desenvolvido com ❤️ usando [Tauri](https://tauri.app), [Angular](https://angular.io), e [Docker](https://docker.com)**

# GitHub Actions CI/CD para Globo Monitor

Este diretório contém workflows do GitHub Actions para build e release automatizados.

## Workflow: Build and Release

### Triggers
- **Push** para branches `main` ou `master`
- **Tags** com formato `v*` (ex: `v1.0.0`)
- **Pull Requests** para `main` ou `master`
- **Manual** via workflow_dispatch

### Plataformas Suportadas

#### Linux (Ubuntu 22.04)
- **Formatos**: `.deb`, `.rpm`, `.AppImage`
- **Arquitetura**: x86_64

#### Windows (Latest)
- **Formatos**: `.exe` (NSIS), `.msi`
- **Arquitetura**: x86_64

#### macOS (Latest)
- **Formatos**: `.dmg`, `.app`
- **Arquitetura**: Universal (Intel + Apple Silicon)

## Como Usar

### 1. Build Automático (Push/PR)
Simplesmente faça push para `main` ou abra um Pull Request. Os artifacts estarão disponíveis na aba "Actions" do GitHub.

### 2. Release com Tag
```bash
# Criar e push de uma tag
git tag v1.0.0
git push origin v1.0.0
```

Isso irá:
- Compilar para todas as plataformas
- Criar um draft release no GitHub
- Anexar todos os instaladores ao release

### 3. Build Manual
1. Vá para a aba "Actions" no GitHub
2. Selecione "Build and Release"
3. Clique em "Run workflow"
4. Escolha a branch e execute

## Configuração de Secrets (Opcional)

### Para Assinatura de Código macOS
Se você tiver uma conta Apple Developer, configure estes secrets:

```
APPLE_CERTIFICATE          # Certificado em base64
APPLE_CERTIFICATE_PASSWORD # Senha do certificado
APPLE_SIGNING_IDENTITY     # Nome do certificado
APPLE_ID                   # Apple ID
APPLE_PASSWORD             # App-specific password
APPLE_TEAM_ID              # Team ID
```

**Nota**: Sem estes secrets, o build macOS ainda funcionará, mas o app não será assinado.

### Para Assinatura de Código Windows (Opcional)
```
WINDOWS_CERTIFICATE        # Certificado em base64
WINDOWS_CERTIFICATE_PASSWORD # Senha do certificado
```

## Artifacts

### Builds sem Tag
Os artifacts ficam disponíveis por 90 dias na aba "Actions" > "Build and Release" > (workflow específico).

### Releases com Tag
Os instaladores ficam permanentemente anexados ao release criado.

## Estrutura de Artifacts

```
globo-monitor-ubuntu-22.04/
  ├── globo-monitor_X.X.X_amd64.deb
  ├── globo-monitor-X.X.X-1.x86_64.rpm
  └── globo-monitor_X.X.X_amd64.AppImage

globo-monitor-windows-latest/
  ├── globo-monitor_X.X.X_x64_en-US.msi
  └── globo-monitor_X.X.X_x64-setup.exe

globo-monitor-macos-latest/
  ├── globo-monitor_X.X.X_universal.dmg
  └── globo-monitor.app/
```

## Troubleshooting

### Build Falha no Linux
- Verifique se todas as dependências estão no workflow
- Confirme que o `tauri.conf.json` está correto

### Build Falha no macOS
- Builds sem assinatura podem ter warnings (normal)
- Para distribuição, configure os secrets da Apple

### Build Falha no Windows
- Verifique o `tauri.conf.json` para configurações Windows
- Certifique-se que os ícones `.ico` existem

## Próximos Passos

1. **Primeiro Build**: Faça push para testar o workflow
2. **Ajustar Versão**: Atualize `version` no `tauri.conf.json`
3. **Criar Release**: Use tags para releases oficiais
4. **Configurar Assinatura**: (Opcional) Para distribuição profissional

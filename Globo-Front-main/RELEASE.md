# Globo Monitor - Guia de Release

## Processo de Release

### 1. Preparação

#### Atualizar Versão
Edite `src-tauri/tauri.conf.json`:
```json
{
  "version": "1.0.0"  // Atualize aqui
}
```

Edite `src-tauri/Cargo.toml`:
```toml
[package]
version = "1.0.0"  # Atualize aqui
```

#### Atualizar Changelog (Opcional)
Crie/atualize `CHANGELOG.md` com as mudanças da versão.

### 2. Criar Tag e Release

```bash
# Commit das mudanças de versão
git add src-tauri/tauri.conf.json src-tauri/Cargo.toml
git commit -m "chore: bump version to v1.0.0"

# Criar tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push da tag (isso inicia o build automático)
git push origin v1.0.0
```

### 3. Monitorar Build

1. Vá para **Actions** no GitHub
2. Aguarde os builds terminarem (~15-20 minutos)
3. Verifique se todos os 3 jobs (Linux, Windows, macOS) passaram

### 4. Publicar Release

1. Vá para **Releases** no GitHub
2. Encontre o draft criado automaticamente
3. Revise os assets anexados:
   - ✅ `.deb` e `.rpm` (Linux)
   - ✅ `.exe` e `.msi` (Windows)
   - ✅ `.dmg` (macOS)
4. Edite a descrição do release
5. Clique em **Publish release**

## Instaladores Gerados

### Linux
- **Debian/Ubuntu**: `globo-monitor_X.X.X_amd64.deb`
  ```bash
  sudo dpkg -i globo-monitor_X.X.X_amd64.deb
  ```
  
- **Fedora/RHEL**: `globo-monitor-X.X.X-1.x86_64.rpm`
  ```bash
  sudo rpm -i globo-monitor-X.X.X-1.x86_64.rpm
  ```

- **AppImage**: `globo-monitor_X.X.X_amd64.AppImage`
  ```bash
  chmod +x globo-monitor_X.X.X_amd64.AppImage
  ./globo-monitor_X.X.X_amd64.AppImage
  ```

### Windows
- **MSI Installer**: `globo-monitor_X.X.X_x64_en-US.msi`
  - Duplo clique para instalar
  - Instalador tradicional do Windows

- **NSIS Installer**: `globo-monitor_X.X.X_x64-setup.exe`
  - Instalador mais leve
  - Duplo clique para instalar

### macOS
- **DMG**: `globo-monitor_X.X.X_universal.dmg`
  - Duplo clique no DMG
  - Arraste para Applications
  - Suporta Intel e Apple Silicon

## Versionamento Semântico

Use [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Mudanças incompatíveis
- **MINOR** (0.1.0): Novas funcionalidades compatíveis
- **PATCH** (0.0.1): Correções de bugs

Exemplos:
- `v1.0.0` - Primeiro release estável
- `v1.1.0` - Nova funcionalidade
- `v1.1.1` - Correção de bug
- `v2.0.0` - Breaking changes

## Assinatura de Código (Opcional)

### macOS
Para distribuir fora da App Store:

1. **Obter Certificado**:
   - Inscreva-se no Apple Developer Program ($99/ano)
   - Crie um Developer ID Application certificate

2. **Configurar Secrets no GitHub**:
   ```
   APPLE_CERTIFICATE          # Certificado exportado em base64
   APPLE_CERTIFICATE_PASSWORD # Senha do certificado
   APPLE_SIGNING_IDENTITY     # "Developer ID Application: Seu Nome"
   APPLE_ID                   # seu@email.com
   APPLE_PASSWORD             # App-specific password
   APPLE_TEAM_ID              # ID do time (10 caracteres)
   ```

3. **Exportar Certificado**:
   ```bash
   # No macOS, exportar do Keychain Access
   # Converter para base64
   base64 -i certificate.p12 | pbcopy
   ```

### Windows
Para assinatura de código Windows:

1. Obter certificado de Code Signing
2. Configurar secrets:
   ```
   WINDOWS_CERTIFICATE
   WINDOWS_CERTIFICATE_PASSWORD
   ```

## Troubleshooting

### Build Falha
- Verifique os logs no GitHub Actions
- Teste localmente: `npx tauri build`
- Verifique se a versão está correta em todos os arquivos

### Release Não Aparece
- Confirme que a tag foi criada: `git tag -l`
- Confirme que a tag foi enviada: `git ls-remote --tags origin`
- Verifique se o workflow foi executado na aba Actions

### Instalador Não Funciona
- **macOS**: "App is damaged" → Usuário precisa permitir em System Preferences
- **Windows**: SmartScreen warning → Normal para apps não assinados
- **Linux**: Dependências faltando → Documentar requisitos

## Checklist de Release

- [ ] Versão atualizada em `tauri.conf.json`
- [ ] Versão atualizada em `Cargo.toml`
- [ ] CHANGELOG.md atualizado (se aplicável)
- [ ] Testes locais passando
- [ ] Commit e push das mudanças
- [ ] Tag criada e enviada
- [ ] GitHub Actions build completo
- [ ] Todos os instaladores gerados
- [ ] Release draft revisado
- [ ] Release publicado
- [ ] Anúncio do release (se aplicável)

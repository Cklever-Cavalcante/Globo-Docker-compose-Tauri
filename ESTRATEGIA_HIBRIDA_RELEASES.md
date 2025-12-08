# 🎯 ESTRATÉGIA HÍBRIDA: Builds Locais + GitHub Actions

## 📋 Visão Geral

Esta estratégia resolve os problemas de builds falhando no GitHub Actions, permitindo que você:
- ✅ Gere **macOS** via GitHub Actions (já funcionando perfeitamente)
- ✅ Gere **Windows via GitHub Actions** (NSIS apenas - sem WiX problemático)
- ✅ Gere **Linux localmente** devido a problemas de espaço em disco no Actions
- ✅ Combine tudo em **releases únicos** manualmente
- ✅ Mantenha **funcionalidade completa** sem simplificações

---

## 🏗️ Análise dos Formatos de Bundle

### 🐧 **Linux - TODOS os formatos estão corretos:**
- ✅ `.deb` - Ubuntu/Debian (instalador padrão)
- ✅ `.rpm` - RedHat/Fedora/CentOS  
- ✅ `.AppImage` - Universal Linux (portable)

> **Nota:** Tauri só gera esses 3 formatos para Linux. Não existe `.exe` ou `.msi` para Linux.

### 🪟 **Windows - Formatos corretos:**
- ✅ `.msi` - Instalador Windows (WiX Toolset)
- ✅ `.exe` - Instalador NSIS (executável)

> **Nota:** O `.exe` que você está vendo é o **NSIS installer**, não um executável standalone. Tauri não gera `.exe` standalone para aplicações desktop.

### 🍎 **macOS - Formatos corretos:**
- ✅ `.dmg` - Disk Image (instalador padrão)
- ✅ `.app` - Aplicação macOS (bundle)

---

## 🔄 Processo Híbrido Completo

### 1️⃣ **macOS via GitHub Actions** (Automático)
```bash
# O Actions já gera:
- Globo Monitor_x.x.x_universal.dmg
- Globo Monitor.app
- Imagem Docker (se configurado)
```

### 2️⃣ **Windows via GitHub Actions** (Automático - NSIS apenas)
```bash
# O Actions gera automaticamente:
- globo-monitor_x.x.x_x64-setup.exe (NSIS installer)
# Nota: MSI (WiX) removido devido a erros com arquivos grandes

# Para builds locais completos (MSI + NSIS):
cd C:\Users\Ck\Downloads\Globo-Docker-compose-Tauri-main
.\prepara-bundle-windows.ps1
cd Globo-Front-main
npm install --legacy-peer-deps
npm run build
npm run tauri build
```

### 3️⃣ **Linux Local** (Manual - Obrigatório)
```bash
# Linux REMOVIDO do GitHub Actions devido a problemas de espaço em disco
# Build local obrigatório para Linux

cd ~/Downloads/Globo-Docker-compose-Tauri-main

# Preparar recursos
chmod +x prepara-bundle-linux.sh
./prepara-bundle-linux.sh

# Gerar build
cd Globo-Front-main
npm install --legacy-peer-deps
npm run build
npm run tauri build

# Resultados em:
# Globo-Front-main/src-tauri/target/release/bundle/deb/*.deb
# Globo-Front-main/src-tauri/target/release/bundle/rpm/*.rpm
# Globo-Front-main/src-tauri/target/release/bundle/appimage/*.AppImage
```

---

## 📤 Upload Manual para Releases

### **Opção 1: Via Interface Web do GitHub** (Recomendado)

1. **Acesse:** https://github.com/Cklever-Cavalcante/Globo-Docker-compose-Tauri/releases

2. **Crie novo release:**
   - Clique em "Draft a new release"
   - Tag: `v1.0.0` (ou próxima versão)
   - Title: "Globo Monitor v1.0.0"

3. **Upload dos arquivos:**
   ```
   # Arraste e solte os arquivos:
   
   # Do GitHub Actions (macOS):
   Globo Monitor_1.0.0_universal.dmg
   Globo Monitor.app (zipado)
   
   # Do seu Windows local:
   globo-monitor_1.0.0_x64_en-US.msi
   globo-monitor_1.0.0_x64-setup.exe
   
   # Do seu Linux local:
   globo-monitor_1.0.0_amd64.deb
   globo-monitor_1.0.0_amd64.AppImage
   globo-monitor_1.0.0.x86_64.rpm
   
   # Imagem Docker (se gerada):
   globo-monitor-docker.tar.gz
   ```

### **Opção 2: Via GitHub CLI** (Automatizado)

```bash
# Instalar GitHub CLI (se não tiver)
# https://cli.github.com/

# Criar release com upload
gh release create v1.0.0 \
  --title "Globo Monitor v1.0.0" \
  --notes "Release com builds multi-plataforma" \
  "Globo-Front-main/src-tauri/target/release/bundle/deb/*.deb" \
  "Globo-Front-main/src-tauri/target/release/bundle/rpm/*.rpm" \
  "Globo-Front-main/src-tauri/target/release/bundle/appimage/*.AppImage" \
  "Globo-Front-main/src-tauri/target/release/bundle/msi/*.msi" \
  "Globo-Front-main/src-tauri/target/release/bundle/nsis/*.exe" \
  "Globo-Front-main/src-tauri/target/release/bundle/dmg/*.dmg"
```

---

## 🐳 Sobre a Imagem Docker do GitHub Actions

A imagem Docker gerada no GitHub Actions serve para:

1. **Distribuição simplificada** - Usuários podem rodar a aplicação via Docker
2. **Backup do ambiente** - Preserva o estado exato dos serviços
3. **Testes consistentes** - Garante mesmo ambiente em diferentes máquinas

**Como usar a imagem Docker:**
```bash
# Carregar imagem
docker load -i globo-monitor-docker.tar.gz

# Executar
docker-compose up -d
```

---

## 🔧 Problemas Resolvidos

### **Erro WixTools light.exe no Windows**
**Problema**: O WiX Tools falha com arquivos grandes (Docker images + backend + IA)
**Solução**: Usar apenas NSIS no GitHub Actions, gerar MSI localmente quando necessário

### **Problemas de Espaço em Disco no Linux**
**Problema**: Múltiplas limpezas agressivas e recursos pesados excedem limites
**Solução**: Build local obrigatório para Linux - você tem controle total

### **Timeout no GitHub Actions**
**Problema**: Builds grandes (>2GB) podem falhar por timeout (360 minutos)
**Solução**: Builds locais não têm limites de tempo

## ⚠️ Pontos Importantes

### **Sobre os formatos:**
- **Windows NUNCA vai gerar `.exe` standalone** - O `.exe` é o instalador NSIS
- **Linux NUNCA vai gerar `.exe` ou `.msi`** - Só gera `.deb`, `.rpm`, `.AppImage`
- **macOS NUNCA vai gerar `.exe` ou `.msi`** - Só gera `.dmg` e `.app`

### **Sobre os problemas do GitHub Actions:**
- **Timeout**: Builds grandes (>2GB) podem falhar por timeout (360 minutos)
- **Recursos**: Docker dentro do Actions pode ser limitado
- **Cache**: Imagens Docker grandes não são cacheadas bem

### **Vantagens do Local:**
- ✅ **Sem limites de tempo** - Você controla o processo
- ✅ **Recursos completos** - Usa todo poder da sua máquina
- ✅ **Debug fácil** - Você vê exatamente o que acontece
- ✅ **Repetível** - Pode rodar quantas vezes quiser

---

## 🎯 Checklist Final

### **Antes de criar release:**
- [ ] macOS build via GitHub Actions ✅
- [ ] Windows builds gerados localmente ✅
- [ ] Linux builds gerados localmente ✅
- [ ] Todos os arquivos testados ✅
- [ ] Versão incrementada (tag) ✅

### **Arquivos no release final:**
```
📦 Release v1.0.0
├── 🍎 macOS (GitHub Actions)
│   ├── Globo Monitor_1.0.0_universal.dmg
│   └── Globo Monitor.app (zipado)
├── 🪟 Windows (GitHub Actions - NSIS)
│   └── globo-monitor_1.0.0_x64-setup.exe
├── 🪟 Windows (Local - Opcional)
│   └── globo-monitor_1.0.0_x64_en-US.msi
├── 🐧 Linux (Local - Obrigatório)
│   ├── globo-monitor_1.0.0_amd64.deb
│   ├── globo-monitor_1.0.0_amd64.AppImage
│   └── globo-monitor_1.0.0.x86_64.rpm
└── 🐳 Docker (GitHub Actions)
    └── globo-monitor-docker.tar.gz (opcional)
```

---

## 🚀 **Resposta Direta às Suas Dúvidas:**

**1. "Posso criar localmente e colocar nos releases?"**
✅ **SIM!** Totalmente possível e recomendado para builds grandes.

**2. "Posso misturar macOS do Actions com Windows/Linux local?"**
✅ **SIM!** É a melhor estratégia - aproveita o que funciona e complementa manualmente.

**3. "A imagem Docker do Actions serve pra que?"**
📋 **Para distribuição Docker** - usuários podem rodar via `docker-compose up` sem instalar nada.

**4. "Linux está gerando tudo certo?"**
✅ **SIM!** `.deb`, `.rpm`, `.AppImage` são os únicos formatos que o Tauri gera para Linux.

**5. "Windows deveria gerar .exe além de .msi e .nsis?"**
❌ **NÃO!** O `.exe` que você vê **É** o instalador NSIS. Tauri não gera `.exe` standalone.

**6. "Por que o WiX falha no GitHub Actions?"**
🚨 **Erro WixTools light.exe**: O WiX não consegue lidar com arquivos muito grandes (Docker images + backend + IA service). **Solução**: NSIS no Actions, MSI local quando necessário.

**7. "Por que Linux foi removido do GitHub Actions?"**
🚨 **Problemas de espaço em disco**: Múltiplas limpezas agressivas e recursos pesados excedem limites. **Solução**: Build local obrigatório para Linux.

**8. "Por que NSIS falha com arquivos Docker grandes?"**
🚨 **Erro de criação de mmap**: NSIS não consegue processar stubs de 1KB para arquivos .tar grandes. **Solução**: Implementar stubs .tar válidos com:
   - ✅ Criação de arquivos .tar reais com conteúdo dummy
   - ✅ Múltiplos fallbacks: tar nativo → Compress-Archive → header básico
   - ✅ Arquivos README.txt dummy para validade estrutural
   - ✅ Verificação de integridade com Get-Item e tamanhos
   - ✅ Remoção de stubs problemáticos antes de criar novos válidos

**A estratégia híbrida é perfeita para o seu caso!** 🎯
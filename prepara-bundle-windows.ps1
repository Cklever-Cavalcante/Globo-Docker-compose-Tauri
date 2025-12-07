# 🔧 Script de Preparação de Bundle Completo para Windows
# Este script prepara todos os recursos necessários para build Tauri completo

Write-Host "🚀 Iniciando preparação de bundle completo..." -ForegroundColor Green

# Função para verificar comando
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Verificar Docker
Write-Host "Verificando Docker..." -ForegroundColor Yellow
if (-not (Test-Command "docker")) {
    Write-Error "Docker não encontrado. Instale o Docker Desktop primeiro."
    exit 1
}

# Verificar espaço em disco
Write-Host "Verificando espaço em disco..." -ForegroundColor Yellow
$drive = Get-Location | Select-Object -ExpandProperty Drive
$disk = Get-PSDrive $drive
$availableGB = [math]::Round($disk.Free / 1GB, 2)
if ($availableGB -lt 10) {
    Write-Warning "Espaço em disco pode ser insuficiente. Disponível: ${availableGB}GB. Recomendado: 10GB+"
}

# Criar estrutura de diretórios
Write-Host "Criando estrutura de diretórios..." -ForegroundColor Yellow
$resourcesDir = "Globo-Front-main\src-tauri\resources"
$dockerImagesDir = "$resourcesDir\docker-images"

New-Item -ItemType Directory -Force -Path $dockerImagesDir
New-Item -ItemType Directory -Force -Path "$resourcesDir\residencia4-backend-master"
New-Item -ItemType Directory -Force -Path "$resourcesDir\residencia4-ia-main"

# Copiar arquivos de configuração
Write-Host "Copiando arquivos de configuração..." -ForegroundColor Yellow
try {
    Copy-Item "docker-compose.yml" "$resourcesDir\" -Force
    Copy-Item ".env" "$resourcesDir\" -Force
    Write-Host "✅ Arquivos de configuração copiados" -ForegroundColor Green
} catch {
    Write-Error "Falha ao copiar arquivos de configuração: $($_.Exception.Message)"
}

# Copiar backend completo
Write-Host "Copiando backend completo..." -ForegroundColor Yellow
if (Test-Path "residencia4-backend-master") {
    try {
        Copy-Item "residencia4-backend-master\*" "$resourcesDir\residencia4-backend-master\" -Recurse -Force
        Write-Host "✅ Backend copiado" -ForegroundColor Green
    } catch {
        Write-Warning "Falha ao copiar backend: $($_.Exception.Message)"
    }
} else {
    Write-Warning "Diretório residencia4-backend-master não encontrado"
}

# Copiar serviço IA completo
Write-Host "Copiando serviço IA..." -ForegroundColor Yellow
if (Test-Path "residencia4-ia-main") {
    try {
        Copy-Item "residencia4-ia-main\*" "$resourcesDir\residencia4-ia-main\" -Recurse -Force
        Write-Host "✅ Serviço IA copiado" -ForegroundColor Green
    } catch {
        Write-Warning "Falha ao copiar serviço IA: $($_.Exception.Message)"
    }
} else {
    Write-Warning "Diretório residencia4-ia-main não encontrado"
}

# Build e exportar imagens Docker
Write-Host "Construindo imagens Docker..." -ForegroundColor Yellow

# PostgreSQL (imagem oficial)
$postgresTar = "$dockerImagesDir\postgres.tar"
if (-not (Test-Path $postgresTar)) {
    Write-Host "Baixando e exportando PostgreSQL..." -ForegroundColor Yellow
    docker pull postgres:15-alpine
    docker save postgres:15-alpine -o $postgresTar
    $size = (Get-Item $postgresTar).Length / 1MB
    Write-Host "✅ PostgreSQL exportado ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "PostgreSQL já existe, pulando..." -ForegroundColor Gray
}

# Backend API
if (Test-Path "residencia4-backend-master") {
    $backendTar = "$dockerImagesDir\backend.tar"
    if (-not (Test-Path $backendTar)) {
        Write-Host "Construindo e exportando Backend API..." -ForegroundColor Yellow
        Set-Location "residencia4-backend-master"
        docker build -t globo-backend:latest .
        docker save globo-backend:latest -o "..\$backendTar"
        Set-Location ..
        $size = (Get-Item $backendTar).Length / 1MB
        Write-Host "✅ Backend API exportado ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
    } else {
        Write-Host "Backend API já existe, pulando..." -ForegroundColor Gray
    }
}

# IA Service
if (Test-Path "residencia4-ia-main") {
    $iaTar = "$dockerImagesDir\ia-service.tar"
    if (-not (Test-Path $iaTar)) {
        Write-Host "Construindo e exportando IA Service..." -ForegroundColor Yellow
        Set-Location "residencia4-ia-main"
        docker build -t globo-ia:latest .
        docker save globo-ia:latest -o "..\$iaTar"
        Set-Location ..
        $size = (Get-Item $iaTar).Length / 1MB
        Write-Host "✅ IA Service exportado ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
    } else {
        Write-Host "IA Service já existe, pulando..." -ForegroundColor Gray
    }
}

# Verificar tamanho total
Write-Host "Verificando tamanho total dos recursos..." -ForegroundColor Yellow
$totalSize = (Get-ChildItem $resourcesDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "📦 Tamanho total dos recursos: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Cyan

# Listar conteúdo
Write-Host "📁 Recursos:" -ForegroundColor Cyan
Get-ChildItem $resourcesDir | Format-Table Name, @{Name="Size (MB)";Expression={[math]::Round($_.Length/1MB, 2)}}, LastWriteTime

Write-Host "📦 Imagens Docker:" -ForegroundColor Cyan
Get-ChildItem $dockerImagesDir | Format-Table Name, @{Name="Size (MB)";Expression={[math]::Round($_.Length/1MB, 2)}}, LastWriteTime

# Verificar integridade
Write-Host "Verificando integridade dos arquivos..." -ForegroundColor Yellow
$tarFiles = Get-ChildItem "$dockerImagesDir\*.tar"
foreach ($file in $tarFiles) {
    try {
        $result = docker load -i $file.FullName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $($file.Name) - OK" -ForegroundColor Green
        } else {
            Write-Host "❌ $($file.Name) - CORROMPIDO" -ForegroundColor Red
        }
    } catch {
        Write-Host "⚠️ $($file.Name) - Não pôde ser verificado" -ForegroundColor Yellow
    }
}

Write-Host "Preparação concluída! ✅" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Próximos passos:" -ForegroundColor Yellow
Write-Host "1. cd Globo-Front-main"
Write-Host "2. npm install --legacy-peer-deps"
Write-Host "3. npm run build"
Write-Host "4. cargo tauri build"
Write-Host ""
Write-Host "📋 Arquivos preparados:" -ForegroundColor Cyan
Write-Host "   - docker-compose.yml"
Write-Host "   - .env"
Write-Host "   - Backend Python completo"
Write-Host "   - Serviço IA completo"
Write-Host "   - Imagens Docker (PostgreSQL, Backend, IA)"
Write-Host ""
Write-Host "⚠️  Importante: Certifique-se de ter pelo menos 8GB de RAM disponível para o build" -ForegroundColor Yellow
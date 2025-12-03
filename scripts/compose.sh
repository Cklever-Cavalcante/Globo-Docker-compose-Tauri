#!/bin/bash

# Script para detectar e usar docker-compose ou podman-compose
# Compatível com ambos os ambientes

set -e

# Detectar qual ferramenta está disponível
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "✓ Usando docker-compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
    echo "✓ Usando podman-compose"
else
    echo "❌ Erro: Nem docker-compose nem podman-compose foram encontrados"
    echo "Instale um deles:"
    echo "  - Docker: sudo apt install docker-compose"
    echo "  - Podman: sudo apt install podman-compose"
    exit 1
fi

# Executar comando passado como argumento
$COMPOSE_CMD "$@"

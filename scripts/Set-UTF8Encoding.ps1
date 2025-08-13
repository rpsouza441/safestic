#!/usr/bin/env powershell
# Script para configurar codificacao UTF-8 no PowerShell
# Resolve problemas com acentos quebrados na saida

# Configurar codificacao de entrada e saida para UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# Configurar codepage para UTF-8 (65001)
chcp 65001 | Out-Null

Write-Host "Codificacao configurada para UTF-8" -ForegroundColor Green
Write-Host "Acentos e caracteres especiais devem funcionar corretamente" -ForegroundColor Green
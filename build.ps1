$ErrorActionPreference = "Stop"

Write-Host "== Modia build iniciado ==" -ForegroundColor Cyan

# Paths
$VenvDir = "venv"
$PythonExe = "$VenvDir\Scripts\python.exe"
$PipExe = "$VenvDir\Scripts\pip.exe"

$CfrJar = "libs\cfr.jar"
$ServerJar = "server\HytaleServer.jar"
$OutputDir = "hytale_src"

$Requirements = "requirements.txt"

# -----------------------------
# CFR setup
# -----------------------------
$CfrVersion = "0.152"
$CfrDir = "libs"
$CfrJar = "$CfrDir\cfr.jar"
$CfrUrl = "https://www.benf.org/other/cfr/cfr-$CfrVersion.jar"

function Test-CfrHealthy {
    if (-Not (Test-Path $CfrJar)) { return $false }

    try {
        # Test básico: listar contenido del jar
        jar tf $CfrJar | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host "`n== Verificando CFR ==" -ForegroundColor Cyan

if (-Not (Test-CfrHealthy)) {
    Write-Host "CFR no encontrado o corrupto. Descargando version $CfrVersion..." -ForegroundColor Yellow

    if (-Not (Test-Path $CfrDir)) {
        New-Item -ItemType Directory -Path $CfrDir | Out-Null
    }

    Invoke-WebRequest `
        -Uri $CfrUrl `
        -OutFile $CfrJar `
        -UseBasicParsing

    Write-Host "CFR descargado correctamente." -ForegroundColor Green
} else {
    Write-Host "CFR OK. Se reutiliza." -ForegroundColor Green
}
# -----------------------------

function Test-VenvHealthy {
    if (-Not (Test-Path $PythonExe)) { return $false }
    if (-Not (Test-Path $PipExe)) { return $false }

    try {
        & $PythonExe -c "import sys" | Out-Null
        & $PipExe check | Out-Null
        & $PipExe install -r $Requirements --dry-run | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 1. Decompile con CFR
Write-Host "`n[1/4] Decompilando HytaleServer..." -ForegroundColor Yellow
java -jar $CfrJar $ServerJar --outputdir $OutputDir

# 2. Validar / recrear venv
Write-Host "`n[2/4] Verificando entorno virtual..." -ForegroundColor Yellow

$VenvOk = Test-VenvHealthy

if (-Not $VenvOk) {
    Write-Host "Entorno virtual inválido o desactualizado. Regenerando venv..." -ForegroundColor Red

    if (Test-Path $VenvDir) {
        Remove-Item -Recurse -Force $VenvDir
    }

    python -m venv $VenvDir
    & $PipExe install --upgrade pip
    & $PipExe install -r $Requirements
} else {
    Write-Host "Entorno virtual OK. Se reutiliza." -ForegroundColor Green
}

# 3. Ejecutar scripts
Write-Host "`n[3/4] Ejecutando extractChunks.py..." -ForegroundColor Yellow
& $PythonExe utils\extractChunks.py

Write-Host "`n[4/4] Ejecutando buildDB.py..." -ForegroundColor Yellow
& $PythonExe utils\buildDB.py

Write-Host "`n== Build completado con exito ==" -ForegroundColor Green

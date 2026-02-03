.PHONY: all decompile venv check-venv install repos chunks db run clean cfr

PYTHON = python3
VENV_DIR = venv
VENV_PY = $(VENV_DIR)/bin/python
VENV_PIP = $(VENV_DIR)/bin/pip

CFR_VERSION = 0.152
CFR_JAR = libs/cfr.jar
CFR_URL = https://www.benf.org/other/cfr/cfr-$(CFR_VERSION).jar


CFR_JAR = libs/cfr.jar
SERVER_JAR = server/HytaleServer.jar
OUTPUT_DIR = hytale_src
REQ = requirements.txt

all: decompile venv install repos run

# -------------------------
# Decompile
# -------------------------

cfr:
	@mkdir -p libs
	@if [ ! -f "$(CFR_JAR)" ] || ! jar tf "$(CFR_JAR)" >/dev/null 2>&1; then \
		echo "== Descargando CFR $(CFR_VERSION) =="; \
		curl -L "$(CFR_URL)" -o "$(CFR_JAR)"; \
	fi

decompile: cfr
	@echo "== Decompilando con CFR =="
	java -jar $(CFR_JAR) $(SERVER_JAR) --outputdir $(OUTPUT_DIR)

# -------------------------
# Venv
# -------------------------
venv:
	@echo "== Verificando entorno virtual =="
	@if [ ! -x "$(VENV_PY)" ]; then \
		echo "Venv inexistente. Creando..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi

check-venv:
	@echo "== Chequeando dependencias =="
	@if ! $(VENV_PIP) check >/dev/null 2>&1; then \
		echo "Dependencias rotas. Rehaciendo venv..."; \
		rm -rf $(VENV_DIR); \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi

install: venv check-venv
	@echo "== Instalando dependencias =="
	$(VENV_PIP) install -r $(REQ)

# -------------------------
# Repos
# -------------------------
repos:
	@echo "== Clonando repositorios de repository/repos.txt =="
	$(VENV_PY) utils/cloneRepos.py

# -------------------------
# Run
# -------------------------
run: chunks db

chunks: repos
	@echo "== Ejecutando extractChunks.py =="
	$(VENV_PY) utils/extractChunks.py

db:
	@echo "== Ejecutando buildDB.py =="
	$(VENV_PY) utils/buildDB.py

# -------------------------
# Clean
# -------------------------
clean:
	rm -rf $(VENV_DIR) $(OUTPUT_DIR)

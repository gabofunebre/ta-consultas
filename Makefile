SHELL := /bin/bash
.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
COMPOSE ?= docker compose
APP_SERVICE ?= app
DB_SERVICE ?= db
ENV_FILE ?= .env
ENV_EXAMPLE ?= .env.example
DOCKER_NETWORK ?= TA_tunn_net

# -----------------------------------------------------------------------------
# Helpers visuales
# -----------------------------------------------------------------------------
BOLD := \033[1m
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# -----------------------------------------------------------------------------
# Targets
# -----------------------------------------------------------------------------
.PHONY: help makehelp doctor init env network build up down stop start restart rebuild \
        ps logs logs-app logs-db pull shell-app shell-db db-cli exec-app exec-db \
        status clean reset-db reset-all

help: makehelp ## Alias de makehelp.

makehelp: ## Muestra esta ayuda completa.
	@echo -e "$(BOLD)TA Consultas · Makefile de desarrollo$(RESET)"
	@echo -e "$(BLUE)Uso:$(RESET) make <target>"
	@echo
	@echo -e "$(BLUE)Primeros pasos recomendados$(RESET)"
	@echo "  1) make init      # prepara .env y red externa"
	@echo "  2) make up        # build + levanta servicios"
	@echo "  3) make logs-app  # sigue logs de la app"
	@echo
	@echo -e "$(BLUE)Comandos disponibles$(RESET)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  $(GREEN)%-14s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Setup --------------------------------------------------------------------
doctor: ## Verifica prerequisitos (docker y docker compose plugin).
	@command -v docker >/dev/null || { echo -e "$(RED)✖ Docker no está instalado$(RESET)"; exit 1; }
	@docker compose version >/dev/null || { echo -e "$(RED)✖ Falta docker compose plugin$(RESET)"; exit 1; }
	@echo -e "$(GREEN)✔ Entorno Docker OK$(RESET)"

env: ## Crea .env desde .env.example si no existe.
	@if [ -f $(ENV_FILE) ]; then \
		echo -e "$(YELLOW)ℹ $(ENV_FILE) ya existe, no se modifica$(RESET)"; \
	else \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo -e "$(GREEN)✔ $(ENV_FILE) creado desde $(ENV_EXAMPLE)$(RESET)"; \
	fi

network: ## Crea la red externa TA_tunn_net si no existe.
	@docker network inspect $(DOCKER_NETWORK) >/dev/null 2>&1 || docker network create $(DOCKER_NETWORK)
	@echo -e "$(GREEN)✔ Red $(DOCKER_NETWORK) lista$(RESET)"

init: doctor env network ## Inicialización completa del entorno local.
	@echo -e "$(GREEN)✔ Proyecto inicializado$(RESET)"

# --- Ciclo de vida ------------------------------------------------------------
build: ## Construye imágenes de docker compose.
	@$(COMPOSE) build

up: ## Levanta servicios en segundo plano (build incluido).
	@$(COMPOSE) up -d --build

start: ## Inicia servicios existentes sin reconstruir.
	@$(COMPOSE) start

stop: ## Detiene servicios sin remover contenedores.
	@$(COMPOSE) stop

down: ## Baja servicios y remueve contenedores/red interna.
	@$(COMPOSE) down

restart: ## Reinicia servicios.
	@$(COMPOSE) restart

rebuild: ## Rebuild completo (down + build sin cache + up).
	@$(COMPOSE) down
	@$(COMPOSE) build --no-cache
	@$(COMPOSE) up -d

pull: ## Actualiza imágenes remotas declaradas en compose.
	@$(COMPOSE) pull

# --- Observabilidad -----------------------------------------------------------
ps: ## Lista estado de servicios.
	@$(COMPOSE) ps

logs: ## Sigue logs de todos los servicios.
	@$(COMPOSE) logs -f

logs-app: ## Sigue logs de la app.
	@$(COMPOSE) logs -f $(APP_SERVICE)

logs-db: ## Sigue logs de la base de datos.
	@$(COMPOSE) logs -f $(DB_SERVICE)

status: ps ## Alias de ps.

# --- Acceso a contenedores ----------------------------------------------------
shell-app: ## Abre shell bash dentro de app.
	@$(COMPOSE) exec $(APP_SERVICE) bash

shell-db: ## Abre shell bash dentro de db.
	@$(COMPOSE) exec $(DB_SERVICE) bash

db-cli: ## Abre psql en db con POSTGRES_DB/POSTGRES_USER del .env.
	@$(COMPOSE) exec $(DB_SERVICE) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

exec-app: ## Ejecuta comando en app. Uso: make exec-app CMD='python run.py'
	@if [ -z "$(CMD)" ]; then echo -e "$(RED)✖ Falta CMD. Ej: make exec-app CMD='python run.py'$(RESET)"; exit 1; fi
	@$(COMPOSE) exec $(APP_SERVICE) bash -lc "$(CMD)"

exec-db: ## Ejecuta comando en db. Uso: make exec-db CMD='psql -U ...'
	@if [ -z "$(CMD)" ]; then echo -e "$(RED)✖ Falta CMD. Ej: make exec-db CMD='psql -U ...'$(RESET)"; exit 1; fi
	@$(COMPOSE) exec $(DB_SERVICE) bash -lc "$(CMD)"

# --- Limpieza y reseteo -------------------------------------------------------
clean: ## Baja stack y elimina volúmenes huérfanos de compose.
	@$(COMPOSE) down --volumes --remove-orphans

reset-db: ## Reinicia SOLO datos de Postgres (borra ./postgres_data).
	@$(COMPOSE) down
	@rm -rf ./postgres_data/*
	@$(COMPOSE) up -d --build
	@echo -e "$(YELLOW)⚠ Base reiniciada: ./postgres_data fue limpiado$(RESET)"

reset-all: ## Reinicia TODO (db + uploads) y levanta de cero.
	@$(COMPOSE) down
	@rm -rf ./postgres_data/* ./app/uploads/*
	@$(COMPOSE) up -d --build
	@echo -e "$(YELLOW)⚠ Datos reiniciados: postgres_data y app/uploads$(RESET)"

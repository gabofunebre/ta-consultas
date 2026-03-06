# TA Consultas - MVP de seguimiento comercial

Sistema web interno para registrar consultas comerciales (WhatsApp / Email), asignarlas a vendedores y dar seguimiento de estado con historial automático, archivos adjuntos y notas breves.

## 1) Arquitectura propuesta (Fase 1)

### Stack elegido
- **Backend + frontend server-side:** Flask + Jinja2.
- **Base de datos:** PostgreSQL 17 (imagen fijada para evitar cambios incompatibles al usar `latest`).
- **Persistencia de adjuntos:** carpeta montada en volumen (`/app/uploads`).
- **Orquestación:** Docker Compose.

### Justificación breve
- Flask permite un MVP rápido, mantenible y claro.
- Render server-side simplifica la UX (sin complejidad de SPA).
- PostgreSQL ofrece robustez y escalabilidad para crecer.
- Separación app/db mantiene una arquitectura limpia y extensible.

## 2) Estructura de carpetas y modelo de datos (Fase 2)

## Estructura

```text
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   ├── static/
│   │   └── styles.css
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── home.html
│   │   ├── consulta_new.html
│   │   ├── consultas_list.html
│   │   └── consulta_detail.html
│   └── uploads/
├── postgres_data/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
└── .env.example
```

## Modelo de datos

### `users`
- `id`
- `nombre`
- `email`
- `password_hash`
- `role` (`admin` / `vendedor`)
- `activo`
- `created_at`

### `consultas`
- `id`
- `fecha_creacion`
- `canal` (WhatsApp / Email)
- `nombre_contacto`
- `telefono_o_email`
- `texto_consulta`
- `estado_actual` (Nueva, Atendido, Presupuestado, Seguimiento, Ganada, Perdida)
- `responsable_id`
- `observaciones_opcionales`
- `created_at`
- `updated_at`

### `adjuntos`
- `id`
- `consulta_id`
- `nombre_archivo`
- `ruta_archivo`
- `tipo_mime`
- `fecha_subida`
- `usuario_que_subio`

### `historial_actividad`
- `id`
- `consulta_id`
- `usuario_id`
- `tipo_evento`
- `descripcion`
- `fecha`

## 3) MVP funcional implementado (Fase 3)

### Funcionalidades incluidas
- Login simple con sesión.
- Roles `admin` y `vendedor`.
- Creación de consultas (admin).
- Listado de consultas con filtros por estado, responsable y búsqueda.
- Vista “Mis consultas” (vendedor ve solo las suyas).
- Ficha completa de consulta.
- Cambio de estado rápido.
- Reasignación (admin).
- Adjuntos de archivos.
- Notas breves.
- Historial automático de eventos:
  - consulta creada,
  - consulta asignada,
  - estado cambiado,
  - archivo adjuntado,
  - nota agregada.

### UX aplicada
- Tipografía grande.
- Botones grandes.
- Lenguaje claro.
- Pocas acciones por pantalla.
- Estilo sobrio y limpio.

## 4) Ejecución y configuración (Fase 4)

## Requisitos
- Docker + Docker Compose
- Redes Docker externas existentes: `TA_tunn_net` y `TA_internal_net`

Crear redes si no existen:

```bash
docker network create TA_tunn_net
docker network create TA_internal_net
```

## Variables de entorno

1. Copiar `.env.example` a `.env`:

```bash
cp .env.example .env
```

2. Ajustar variables si hace falta.

Variables recomendadas:
- `POSTGRES_*`: las usa el contenedor `db` para inicializar el clúster **solo en el primer arranque**.
- `DB_*`: las usa la app para conectarse a la base (si faltan, usa `POSTGRES_*` como fallback).
- `DATABASE_URL`: si está definida y no está vacía, tiene prioridad sobre `DB_*` y `POSTGRES_*`.

> Sugerencia: si vas a ejecutar la app fuera de Docker Compose, configurá `DB_HOST=localhost` o un `DATABASE_URL` completo apuntando a tu instancia de PostgreSQL.

> Importante: si cambiás `POSTGRES_USER` o `POSTGRES_PASSWORD` después de que `./postgres_data` ya fue inicializada, Postgres mantiene las credenciales viejas. En ese caso, cambiá la contraseña dentro de la base o recreá el volumen/carpeta de datos.

## Levantar el sistema

```bash
docker compose up -d --build
# o equivalente:
make up
```

> **Importante:** este `docker-compose.yml` **no expone puertos al host**, tal como solicitaste.
> La app queda conectada a `TA_tunn_net` y `TA_internal_net`, mientras que la base de datos queda solo en `TA_internal_net`.

Persistencia en carpetas del host (`./`):
- Base de datos: `./postgres_data` (el clúster se inicializa dentro de `./postgres_data/pgdata`)
- Adjuntos: `./app/uploads`


### Nota sobre versión de PostgreSQL
- La imagen quedó fijada en `postgres:17` para evitar rupturas al actualizar automáticamente desde `latest`.
- Si ya tenías datos locales de otra versión y aparece un error de compatibilidad, podés:
  1. Mantener la misma versión que creó ese volumen/carpeta, o
  2. Hacer migración de versión con `pg_upgrade`, o
  3. Si no necesitás los datos, borrar `./postgres_data` y recrear.


### Permisos de `postgres_data` (host bind mount)
Si querés mantener los datos de Postgres dentro del proyecto (`./postgres_data`), el proceso de Postgres dentro del contenedor necesita poder escribir en esa carpeta.

El contenedor oficial de Postgres usa por defecto el usuario `postgres` con **UID:GID `999:999`**.

1. Crear carpeta local:
```bash
mkdir -p ./postgres_data
```

2. Asignar owner/permisos correctos (opción recomendada):
```bash
make fix-db-perms
```

3. Levantar servicios:
```bash
make up
```

Si preferís hacerlo manualmente en Linux:
```bash
sudo chown -R 999:999 ./postgres_data
sudo chmod 700 ./postgres_data
```

> Si tu carpeta del proyecto está en un disco con permisos no POSIX (por ejemplo NTFS montado sin metadata), `chown/chmod` puede no surtir efecto. En ese caso, mové el repo a un filesystem Linux (ext4) o habilitá metadata/ACL en el montaje.

## Usuarios iniciales
Se crean automáticamente al iniciar:
- `admin@ta.local` / `admin123`
- `vendedor@ta.local` / `vendedor123`

## Comandos útiles

Ver logs:
```bash
docker compose logs -f app
```

Reiniciar:
```bash
docker compose restart
```

Bajar servicios:
```bash
docker compose down
```

## Seguridad y mejoras recomendadas
- Cambiar credenciales y `SECRET_KEY` en producción.
- Mover adjuntos a S3/MinIO para alta disponibilidad.
- Agregar migraciones (Flask-Migrate/Alembic).
- Agregar auditoría avanzada y notificaciones en futuras fases.

# TA Consultas - MVP de seguimiento comercial

Sistema web interno para registrar consultas comerciales (WhatsApp / Email), asignarlas a vendedores y dar seguimiento de estado con historial automático, archivos adjuntos y notas breves.

## 1) Arquitectura propuesta (Fase 1)

### Stack elegido
- **Backend + frontend server-side:** Flask + Jinja2.
- **Base de datos:** PostgreSQL (latest).
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
- Red Docker externa existente: `TA_tunn_net`

Crear red si no existe:

```bash
docker network create TA_tunn_net
```

## Variables de entorno

1. Copiar `.env.example` a `.env`:

```bash
cp .env.example .env
```

2. Ajustar variables si hace falta.

## Levantar el sistema

```bash
docker compose up -d --build
```

> **Importante:** este `docker-compose.yml` **no expone puertos al host**, tal como solicitaste. El acceso se realiza por la red compartida `TA_tunn_net` (por ejemplo con cloudflared).

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

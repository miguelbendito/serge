# Serge's Catering - Website

Plataforma web para un servicio de catering de alta gama.

## 🚀 Quick Start

### Prerrequisitos
- **Docker** y **Docker Compose** instalados
- **Python 3.8+**

### 1. Clonar y configurar entorno

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd "serge's website"

# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tus credenciales (opcional para desarrollo local)
```

### 2. Levantar la base de datos (Docker)

```bash
# Iniciar PostgreSQL y Adminer (GUI de base de datos)
docker compose up -d

# Verificar que los contenedores estén corriendo
docker ps
```

**Servicios disponibles:**
- **PostgreSQL**: `localhost:5432`
- **Adminer (GUI)**: [http://localhost:8080](http://localhost:8080)

### 3. Instalar dependencias de Python

```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
python3 main.py
```

La aplicación estará disponible en: **[http://localhost:5001](http://localhost:5001)**

---

## 🗄️ Base de Datos

### Conexión a Adminer (GUI)
1. Ir a [http://localhost:8080](http://localhost:8080)
2. Usar estas credenciales:
   - **System**: PostgreSQL
   - **Server**: `db`
   - **Username**: `admin`
   - **Password**: `password`
   - **Database**: `serge_db`

### Restaurar estructura de la BD
Si necesitas recrear las tablas desde cero, existe un archivo de esquema en:
```
instance/schema.sql
```

Para aplicarlo:
```bash
docker exec -i sergeswebsite-db-1 psql -U admin -d serge_db < instance/schema.sql
```

### Crear usuario administrador
```bash
python3 create_admin_user.py
```
Credenciales por defecto:
- **Email**: `admin@example.com`
- **Password**: `password`

---

## 📧 Configuración de Email

Editar el archivo `.env`:

```env
MAIL_ADDRESS=tu_email@gmail.com
MAIL_APP_PW=tu_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

Para desarrollo local, usa **MailHog** (ya incluido en otros proyectos) o deja los valores por defecto que apuntan a `localhost:1025`.

---

## 🏗️ Estructura del Proyecto

```
├── main.py              # Aplicación Flask principal
├── forms.py             # Formularios WTForms
├── requirements.txt     # Dependencias Python
├── docker-compose.yml   # Configuración Docker
├── .env.example         # Variables de entorno (plantilla)
├── instance/
│   └── schema.sql       # Estructura de la BD exportada
├── static/
│   ├── css/
│   ├── js/
│   └── assets/
└── templates/           # Templates Jinja2
```

---

## 👤 Panel de Administración

1. Ir a `/login`
2. Iniciar sesión con credenciales de admin
3. El usuario con `id=1` tiene privilegios de administrador
4. Acceder a "Manage Menus" desde la barra de navegación

---

## 🛠️ Comandos Útiles

```bash
# Ver logs del servidor
python3 main.py

# Detener Docker
docker compose down

# Ver estado de contenedores
docker ps

# Acceder a la BD desde terminal
docker exec -it sergeswebsite-db-1 psql -U admin -d serge_db
```

---

## 📝 Notas

- La `SECRET_KEY` está hardcodeada para desarrollo. **Cambiarla en producción**.
- Las migraciones de base de datos se manejan con Flask-Migrate (ejecutar `flask db migrate` y `flask db upgrade`).
- El campo `is_active` en menús controla qué menús son visibles públicamente.

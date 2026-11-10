# marcoslaso-devops-practica — Tienda Online API

**Autor:** Marcos Laso García

## Descripción

Aplicación en Python que gestiona una tienda online sencilla a través de una **API REST hecha con FastAPI** (Práctica 2). Permite:

- **Usuarios:** registrar y consultar clientes (con dirección postal) y administradores.
- **Productos:** crear, consultar y eliminar productos genéricos, electrónicos (con meses de garantía) y de ropa (con talla y color), con control de stock.
- **Pedidos:** crear pedidos de un cliente con varias líneas de producto, comprobando que hay stock, y consultar el historial de pedidos de cada cliente.

La lógica de negocio está en la clase `TiendaService` y los modelos siguen el diseño orientado a objetos de la Práctica 1. Además de la API, el proyecto incluye un cliente Python con `requests` y un frontend web que consumen los mismos endpoints.

Este repositorio se usa en la Práctica 3 para trabajar con Git/GitHub (ramas `feature/*` y Pull Requests) y para contenerizar la API con Docker.

## Estructura

```text
├── src/            API REST con FastAPI (servidor)
│   ├── models/      Producto, Usuario y Pedido
│   ├── Services/    TiendaService (lógica de negocio)
│   ├── schemas.py   Esquemas Pydantic de entrada/salida
│   └── main.py      Endpoints de la API
├── cliente/         Cliente Python con requests
├── frontend/        Frontend web (index.html)
├── requirements.txt Dependencias de la API (versiones fijadas)
├── dockerfile       Imagen Docker de la API
└── .dockerignore    Ficheros que no entran en la imagen
```

Ni el cliente ni el frontend importan nada del servidor: todo pasa por los endpoints de la API.

## Docker

La API está contenerizada con la imagen base `python:3.12-slim`. El contenedor instala las dependencias de `requirements.txt`, copia el código de `src/` y ejecuta la API con un usuario sin privilegios (`appuser`), no como root. El cliente y el frontend no entran en la imagen: se ejecutan fuera y se conectan a la API por HTTP.

### Construir la imagen

Desde la raíz del repositorio:

```bash
docker build -t tienda-online-api:1.0 .
```

### Ejecutar el contenedor

```bash
# En primer plano (Ctrl+C para pararlo)
docker run --rm -p 8000:8000 tienda-online-api:1.0

# En segundo plano, con nombre
docker run -d --rm --name tienda-api -p 8000:8000 tienda-online-api:1.0
docker logs tienda-api
docker stop tienda-api

# Cambiando el puerto interno con la variable PORT
docker run --rm -e PORT=9000 -p 9000:9000 tienda-online-api:1.0
```

### Variables de entorno

| Variable | Valor por defecto | Descripción |
| --- | --- | --- |
| `PORT` | `8000` | Puerto en el que escucha uvicorn dentro del contenedor |

La aplicación no usa claves ni secretos.

### Salida esperada y pruebas

Al arrancar, el contenedor muestra:

```text
INFO:     Started server process [7]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Con el contenedor en marcha:

1. Abrir http://localhost:8000/docs: aparece la documentación de Swagger con los endpoints de usuarios, productos y pedidos.
2. Probar con `curl`:
   ```bash
   curl http://localhost:8000/productos          # [] (todavía no hay productos)
   curl -X POST http://localhost:8000/productos \
        -H "Content-Type: application/json" \
        -d '{"tipo": "generico", "nombre": "Taza", "precio": 5.5, "stock": 30}'
   ```
3. Ejecutar el cliente Python contra el contenedor. Todas las peticiones deben devolver `200` o `201`:
   ```bash
   pip install -r cliente/requirements.txt
   python cliente/cliente.py http://localhost:8000
   ```
4. Abrir `frontend/index.html` en el navegador: se conecta a `http://localhost:8000`.

### Descargar la imagen publicada (Docker Hub)

Imagen: https://hub.docker.com/r/marcoslaso/tienda-online-api

```bash
docker pull marcoslaso/tienda-online-api:1.0
docker run --rm -p 8000:8000 marcoslaso/tienda-online-api:1.0
```

Para publicarla después de construirla:

```bash
docker login
docker tag tienda-online-api:1.0 marcoslaso/tienda-online-api:1.0
docker tag tienda-online-api:1.0 marcoslaso/tienda-online-api:latest
docker push marcoslaso/tienda-online-api:1.0
docker push marcoslaso/tienda-online-api:latest
```

## Ejecución sin Docker

### 1. Arrancar la API

```bash
pip install -r requirements.txt
cd src
uvicorn main:app --reload
```

La documentación interactiva queda en http://localhost:8000/docs.

### 2. Cliente Python (requests)

Con la API arrancada, en otra terminal:

```bash
cd cliente
pip install -r requirements.txt
python cliente.py
```

El script crea un usuario, consulta la lista de usuarios, crea varios productos, consulta la lista de productos, crea un pedido y consulta los pedidos del usuario. En cada petición comprueba el código HTTP y procesa el JSON de la respuesta.

La dirección de la API está en la constante `BASE_URL` de `cliente.py`. También se puede pasar al ejecutarlo:

```bash
python cliente.py http://192.168.1.34:8000
```

### 3. Comunicación entre dos equipos

**En el equipo servidor:**

1. Sacar la IP local:
   - macOS: `ipconfig getifaddr en0`
   - Windows: `ipconfig` (campo "Dirección IPv4")
   - Linux: `hostname -I`
2. Arrancar la API para que acepte conexiones de otros equipos de la red. Con `--host 0.0.0.0` escucha en todas las interfaces; sin esa opción solo acepta conexiones del propio equipo (localhost):
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Si el sistema pregunta si se permiten conexiones entrantes a Python, aceptar. En macOS se revisa en Ajustes → Red → Cortafuegos.

**En el otro equipo (en la misma red):**

1. Abrir `http://IP_DEL_SERVIDOR:8000/docs` en el navegador.
2. Ejecutar el cliente apuntando al servidor:
   ```bash
   python cliente.py http://IP_DEL_SERVIDOR:8000
   ```
3. En el servidor, `GET /usuarios` o `GET /productos` muestran los datos creados desde el otro equipo, lo que demuestra que los dos trabajan sobre la misma API.

### 4. Frontend web

Con la API arrancada, abrir `frontend/index.html` en el navegador (doble clic). Si la API está en otro equipo, se escribe su dirección en la caja **Servidor API** de arriba y se pulsa **Conectar**.

Incluye:

| Pestaña | Qué permite |
| --- | --- |
| Productos | Ver el inventario, crear productos (genérico, electrónico, ropa) y eliminarlos |
| Usuarios | Ver los usuarios y crear clientes o administradores |
| Pedidos | Crear un pedido con varios productos y consultar los pedidos de un usuario |

#### Cómo hace las peticiones

Todo el código que habla con la API está en la sección `PETICIONES A LA API` del `<script>` de `index.html`:

- `pedirApi(metodo, ruta, cuerpo)` hace la petición con `fetch()`, envía los datos como JSON, comprueba el código HTTP (`respuesta.ok`) y, si hay error, muestra el `detail` que devuelve FastAPI.
- El objeto `api` tiene una función por endpoint:

| Función | Endpoint |
| --- | --- |
| `api.listarProductos()` | `GET /productos` |
| `api.crearProducto(datos)` | `POST /productos` |
| `api.eliminarProducto(id)` | `DELETE /productos/{producto_id}` |
| `api.listarUsuarios()` | `GET /usuarios` |
| `api.crearUsuario(datos)` | `POST /usuarios` |
| `api.crearPedido(datos)` | `POST /pedidos` |
| `api.pedidosDeUsuario(id)` | `GET /usuarios/{cliente_id}/pedidos` |

El resto del script solo pinta en pantalla los JSON recibidos y lee los formularios.

Para que el navegador permita estas peticiones, la API tiene activado **CORS** (`CORSMiddleware` en `src/main.py`). Sin CORS, el navegador bloquea las peticiones de una página abierta desde otro origen, por ejemplo un fichero local.

## Comprobación final

Los tres clientes (`/docs`, `cliente.py` y el frontend) usan los mismos endpoints y los mismos datos. Por ejemplo, un pedido creado con `cliente.py` aparece en la pestaña **Pedidos** del frontend.

> Los datos se guardan en memoria, así que se pierden al reiniciar la API.

## Flujo de trabajo con Git

- `main`: rama principal con el código estable.
- `feature/<nombre>`: una rama por funcionalidad (por ejemplo `feature/docker`), que se integra en `main` mediante Pull Request.

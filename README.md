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
├── Tienda_online/   API REST con FastAPI (servidor)
│   ├── models/      Producto, Usuario y Pedido
│   ├── Services/    TiendaService (lógica de negocio)
│   ├── schemas.py   Esquemas Pydantic de entrada/salida
│   └── main.py      Endpoints de la API
├── cliente/         Cliente Python con requests
└── frontend/        Frontend web (index.html)
```

Ni el cliente ni el frontend importan nada del servidor: todo pasa por los endpoints de la API.

## 1. Arrancar la API

```bash
cd Tienda_online
pip install -r requirements.txt
uvicorn main:app --reload
```

La documentación interactiva queda en http://localhost:8000/docs.

## 2. Cliente Python (requests)

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

## 3. Comunicación entre dos equipos

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

## 4. Frontend web

Con la API arrancada, abrir `frontend/index.html` en el navegador (doble clic). Si la API está en otro equipo, se escribe su dirección en la caja **Servidor API** de arriba y se pulsa **Conectar**.

Incluye:

| Pestaña | Qué permite |
| --- | --- |
| Productos | Ver el inventario, crear productos (genérico, electrónico, ropa) y eliminarlos |
| Usuarios | Ver los usuarios y crear clientes o administradores |
| Pedidos | Crear un pedido con varios productos y consultar los pedidos de un usuario |

### Cómo hace las peticiones

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

Para que el navegador permita estas peticiones, la API tiene activado **CORS** (`CORSMiddleware` en `Tienda_online/main.py`). Sin CORS, el navegador bloquea las peticiones de una página abierta desde otro origen, por ejemplo un fichero local.

## Comprobación final

Los tres clientes (`/docs`, `cliente.py` y el frontend) usan los mismos endpoints y los mismos datos. Por ejemplo, un pedido creado con `cliente.py` aparece en la pestaña **Pedidos** del frontend.

> Los datos se guardan en memoria, así que se pierden al reiniciar la API.

## Flujo de trabajo con Git

- `main`: rama principal con el código estable.
- `feature/<nombre>`: una rama por funcionalidad (por ejemplo `feature/docker`), que se integra en `main` mediante Pull Request.

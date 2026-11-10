"""Punto de entrada de la aplicacion: API REST de la tienda online con FastAPI.

Practica 2 - Marcos Laso Garcia

Para arrancarla (desde la carpeta Tienda_online):
    uvicorn main:app --reload
Para que otros equipos de la red puedan conectarse:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
y abrir http://127.0.0.1:8000/docs para probar los endpoints.
"""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import schemas
from Services.Tienda_service import (
    ConflictoError,
    DatosInvalidosError,
    NoEncontradoError,
    TiendaService,
)

app = FastAPI(
    title="Tienda Online API",
    description="API REST de la tienda online de la practica 1 (usuarios, productos y pedidos).",
    version="1.0.0",
    openapi_tags=[
        {"name": "Usuarios", "description": "Registro y consulta de clientes y administradores"},
        {"name": "Productos", "description": "Gestion del inventario (generico, electronico y ropa)"},
        {"name": "Pedidos", "description": "Creacion de pedidos e historial de cada cliente"},
    ],
)

# CORS: permite que el frontend (que se abre en el navegador desde otro origen,
# por ejemplo un fichero local o otro puerto) pueda hacer peticiones a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# una unica instancia del servicio para toda la aplicacion (los datos viven en memoria)
tienda = TiendaService()


# Dependencia para obtener el servicio de la tienda
def get_tienda():
    return tienda


# ---------- USUARIOS ----------

@app.post("/usuarios", response_model=schemas.UsuarioRead, status_code=status.HTTP_201_CREATED,
          tags=["Usuarios"])
def create_usuario(usuario: schemas.UsuarioCreate, tienda: TiendaService = Depends(get_tienda)):
    """Registra un nuevo cliente o administrador."""
    try:
        return tienda.registrar_usuario(usuario.tipo, usuario.nombre, usuario.email,
                                        usuario.direccion_postal or "")
    except ConflictoError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@app.get("/usuarios", response_model=list[schemas.UsuarioRead], tags=["Usuarios"])
def read_usuarios(skip: int = 0, limit: int = 10, nombre: str | None = None,
                  tienda: TiendaService = Depends(get_tienda)):
    """Devuelve la lista de usuarios registrados. Con `nombre` filtra por nombre (o parte de el)."""
    return tienda.listar_usuarios(skip=skip, limit=limit, nombre=nombre)


@app.get("/usuarios/{usuario_id}", response_model=schemas.UsuarioRead, tags=["Usuarios"])
def read_usuario(usuario_id: str, tienda: TiendaService = Depends(get_tienda)):
    """Devuelve un usuario concreto."""
    usuario = tienda.buscar_usuario(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


# ---------- PRODUCTOS ----------

@app.post("/productos", response_model=schemas.ProductoRead, response_model_exclude_none=True,
          status_code=status.HTTP_201_CREATED, tags=["Productos"])
def create_producto(producto: schemas.ProductoCreate, tienda: TiendaService = Depends(get_tienda)):
    """Anade un producto generico, electronico o de ropa al inventario."""
    if producto.tipo == "electronico":
        return tienda.anadir_producto_electronico(producto.nombre, producto.precio,
                                                  producto.stock, producto.meses_garantia)
    if producto.tipo == "ropa":
        return tienda.anadir_producto_ropa(producto.nombre, producto.precio, producto.stock,
                                           producto.talla, producto.color)
    return tienda.anadir_producto(producto.nombre, producto.precio, producto.stock)


@app.get("/productos", response_model=list[schemas.ProductoRead], response_model_exclude_none=True,
         tags=["Productos"])
def read_productos(skip: int = 0, limit: int = 10, nombre: str | None = None,
                   tienda: TiendaService = Depends(get_tienda)):
    """Devuelve los productos del inventario. Con `nombre` filtra por nombre (o parte de el)."""
    return tienda.obtener_productos(skip=skip, limit=limit, nombre=nombre)


@app.get("/productos/{producto_id}", response_model=schemas.ProductoRead,
         response_model_exclude_none=True, tags=["Productos"])
def read_producto(producto_id: str, tienda: TiendaService = Depends(get_tienda)):
    """Devuelve un producto concreto."""
    producto = tienda.buscar_producto(producto_id)
    if producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto


@app.delete("/productos/{producto_id}", tags=["Productos"])
def delete_producto(producto_id: str, tienda: TiendaService = Depends(get_tienda)):
    """Elimina un producto del inventario."""
    if not tienda.eliminar_producto(producto_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return {"message": "Producto eliminado correctamente"}


# ---------- PEDIDOS ----------

@app.post("/pedidos", response_model=schemas.PedidoRead, status_code=status.HTTP_201_CREATED,
          tags=["Pedidos"])
def create_pedido(pedido: schemas.PedidoCreate, tienda: TiendaService = Depends(get_tienda)):
    """Crea un pedido comprobando que existen el cliente y los productos y que hay stock."""
    lineas = [(item.producto_id, item.cantidad) for item in pedido.items]
    try:
        return tienda.realizar_pedido(pedido.cliente_id, lineas)
    except NoEncontradoError as error:
        # no existe el cliente o alguno de los productos
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except DatosInvalidosError as error:
        # el usuario no es un cliente (p. ej. un administrador)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except ConflictoError as error:
        # no hay stock suficiente
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@app.get("/usuarios/{cliente_id}/pedidos", response_model=list[schemas.PedidoRead],
         tags=["Pedidos"])
def read_pedidos_cliente(cliente_id: str, tienda: TiendaService = Depends(get_tienda)):
    """Devuelve el historial de pedidos de un cliente, ordenado por fecha."""
    if tienda.buscar_usuario(cliente_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return tienda.listar_pedidos_usuario(cliente_id)

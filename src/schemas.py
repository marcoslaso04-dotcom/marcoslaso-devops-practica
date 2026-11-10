"""Esquemas Pydantic de la API: validan los datos de entrada y dan forma a las respuestas.

Los esquemas *Read* usan from_attributes=True para poder construirse directamente
a partir de los objetos del dominio (Usuario, Producto, Pedido) que devuelve TiendaService.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------- USUARIOS ----------

class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    # sin la libreria email-validator, comprobamos el formato con una expresion regular
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)


# Esquema para crear un usuario
class UsuarioCreate(UsuarioBase):
    tipo: Literal["cliente", "admin"]
    direccion_postal: str | None = Field(default=None, max_length=200)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "nombre": "Hermindo Ozores",
            "email": "hermindo@mail.com",
            "tipo": "cliente",
            "direccion_postal": "Calle Mayor 1, Madrid",
        }
    })

    @model_validator(mode="after")
    def comprobar_direccion(self):
        """Un cliente necesita direccion postal para poder recibir los pedidos."""
        if self.tipo == "cliente" and not (self.direccion_postal or "").strip():
            raise ValueError("Los clientes tienen que tener direccion_postal")
        return self


# Esquema para devolver un usuario
class UsuarioRead(UsuarioBase):
    id: str
    es_admin: bool

    model_config = ConfigDict(from_attributes=True)


# ---------- PRODUCTOS ----------

class ProductoBase(BaseModel):
    tipo: Literal["generico", "electronico", "ropa"]
    nombre: str = Field(min_length=1, max_length=100)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    # atributos que dependen del tipo de producto
    meses_garantia: int | None = Field(default=None, ge=0)
    talla: str | None = Field(default=None, min_length=1, max_length=10)
    color: str | None = Field(default=None, min_length=1, max_length=30)


# Esquema para crear un producto
class ProductoCreate(ProductoBase):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"tipo": "electronico", "nombre": "Movil Samsung", "precio": 400.0,
             "stock": 10, "meses_garantia": 12},
            {"tipo": "ropa", "nombre": "Camiseta basica", "precio": 15.0,
             "stock": 20, "talla": "M", "color": "Negro"},
            {"tipo": "generico", "nombre": "Taza", "precio": 5.5, "stock": 30},
        ]
    })

    @model_validator(mode="after")
    def comprobar_atributos_del_tipo(self):
        """Comprueba que vienen los atributos del tipo y ninguno de otro tipo.

        - generico: solo nombre, precio y stock
        - electronico: ademas meses_garantia
        - ropa: ademas talla y color
        """
        tiene_garantia = self.meses_garantia is not None
        tiene_ropa = self.talla is not None or self.color is not None

        if self.tipo == "electronico":
            if not tiene_garantia:
                raise ValueError("Un producto electronico necesita meses_garantia")
            if tiene_ropa:
                raise ValueError("Un producto electronico no lleva talla ni color")
        elif self.tipo == "ropa":
            if self.talla is None or self.color is None:
                raise ValueError("Un producto de ropa necesita talla y color")
            if tiene_garantia:
                raise ValueError("Un producto de ropa no lleva meses_garantia")
        elif tiene_garantia or tiene_ropa:
            raise ValueError("Un producto generico no lleva meses_garantia, talla ni color")
        return self


# Esquema para devolver un producto (los atributos opcionales solo salen si son de su tipo)
class ProductoRead(ProductoBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


# ---------- PEDIDOS ----------

# Una linea del pedido al crearlo: que producto y cuantas unidades
class PedidoItemCreate(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)


# Esquema para crear un pedido
class PedidoCreate(BaseModel):
    cliente_id: str
    items: list[PedidoItemCreate] = Field(min_length=1)


# Una linea del pedido tal y como se devuelve
class PedidoItemRead(BaseModel):
    producto_id: str
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float


# Esquema para devolver un pedido completo
class PedidoRead(BaseModel):
    id: str
    fecha: datetime
    cliente_id: str
    total: float
    items: list[PedidoItemRead]

    model_config = ConfigDict(from_attributes=True)

"""Clase Pedido de la tienda."""

import uuid
from datetime import datetime
from typing import List, Tuple

from models.Producto import Producto
from models.Usuario import Cliente


class Pedido:
    """Pedido hecho por un cliente con una lista de productos y cantidades."""

    def __init__(self, cliente: Cliente, lineas: List[Tuple[Producto, int]]):
        self.id: str = str(uuid.uuid4())
        self.cliente: Cliente = cliente
        # cada linea es una tupla (producto, cantidad)
        self.lineas: List[Tuple[Producto, int]] = lineas
        self.fecha: datetime = datetime.now()

    def calcular_total(self) -> float:
        """Suma el precio por la cantidad de cada producto del pedido."""
        total = 0.0
        for producto, cantidad in self.lineas:
            total += producto.precio * cantidad
        return total

    # ---- atributos de solo lectura que usa el esquema PedidoRead ----

    @property
    def cliente_id(self) -> str:
        return self.cliente.id

    @property
    def total(self) -> float:
        return self.calcular_total()

    @property
    def items(self) -> List[dict]:
        """Las lineas del pedido en el formato de PedidoItemRead."""
        return [
            {
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "cantidad": cantidad,
                "precio_unitario": producto.precio,
                "subtotal": producto.precio * cantidad,
            }
            for producto, cantidad in self.lineas
        ]

    def __str__(self) -> str:
        texto = f"Pedido [{self.id[:8]}] de {self.cliente.nombre}"
        texto += f" - fecha: {self.fecha.strftime('%d/%m/%Y %H:%M:%S')}\n"
        for producto, cantidad in self.lineas:
            texto += f"   - {producto.nombre} x{cantidad} = {producto.precio * cantidad}EUR\n"
        texto += f"   TOTAL: {self.calcular_total()}EUR"
        return texto

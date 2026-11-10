"""Capa de servicios: aqui se gestionan las operaciones de la tienda."""

from typing import Dict, List, Optional, Tuple

from models.Pedido import Pedido
from models.Producto import Producto, ProductoElectronico, ProductoRopa
from models.Usuario import Usuario, Cliente, Administrador


# ---------- ERRORES DEL SERVICIO ----------
# La API (main.py) captura estas excepciones y las traduce a codigos HTTP.

class TiendaError(Exception):
    """Error generico de la tienda."""


class NoEncontradoError(TiendaError):
    """El usuario o el producto pedido no existe."""


class DatosInvalidosError(TiendaError):
    """Los datos no son validos para la operacion (p. ej. un admin haciendo un pedido)."""


class ConflictoError(TiendaError):
    """La operacion choca con el estado actual (email repetido, sin stock...)."""


class TiendaService:
    """Guarda los usuarios, los productos y los pedidos de la tienda."""

    def __init__(self):
        self.usuarios: List[Usuario] = []
        self.productos: List[Producto] = []
        self.pedidos: List[Pedido] = []

    # ---------- USUARIOS ----------

    def registrar_usuario(self, tipo: str, nombre: str, email: str,
                          direccion: str = "") -> Usuario:
        """Crea un cliente o un administrador y lo guarda en la tienda."""
        for usuario in self.usuarios:
            if usuario.email.lower() == email.lower():
                raise ConflictoError(f"Ya existe un usuario con el email {email}")

        if tipo == "cliente":
            usuario = Cliente(nombre, email, direccion)
        elif tipo == "admin":
            usuario = Administrador(nombre, email)
        else:
            raise DatosInvalidosError("El tipo tiene que ser 'cliente' o 'admin'")

        self.usuarios.append(usuario)
        return usuario

    def buscar_usuario(self, usuario_id: str) -> Optional[Usuario]:
        """Devuelve el usuario con ese id, o None si no existe."""
        for usuario in self.usuarios:
            if usuario.id == usuario_id:
                return usuario
        return None

    def listar_usuarios(self, skip: int = 0, limit: int = 10,
                        nombre: Optional[str] = None) -> List[Usuario]:
        """Devuelve los usuarios registrados, paginados con skip y limit.

        Si se pasa nombre, solo devuelve los usuarios cuyo nombre lo contiene
        (sin distinguir mayusculas y minusculas).
        """
        usuarios = self.usuarios
        if nombre:
            usuarios = [u for u in usuarios if nombre.lower() in u.nombre.lower()]
        return usuarios[skip:skip + limit]

    # ---------- PRODUCTOS ----------

    def anadir_producto(self, nombre: str, precio: float, stock: int) -> Producto:
        """Crea un producto generico y lo mete en el inventario."""
        producto = Producto(nombre, precio, stock)
        self.productos.append(producto)
        return producto

    def anadir_producto_electronico(self, nombre: str, precio: float, stock: int,
                                    meses_garantia: int) -> ProductoElectronico:
        """Crea un producto electronico y lo mete en el inventario."""
        producto = ProductoElectronico(nombre, precio, stock, meses_garantia)
        self.productos.append(producto)
        return producto

    def anadir_producto_ropa(self, nombre: str, precio: float, stock: int,
                             talla: str, color: str) -> ProductoRopa:
        """Crea un producto de ropa y lo mete en el inventario."""
        producto = ProductoRopa(nombre, precio, stock, talla, color)
        self.productos.append(producto)
        return producto

    def buscar_producto(self, producto_id: str) -> Optional[Producto]:
        """Devuelve el producto con ese id, o None si no existe."""
        for producto in self.productos:
            if producto.id == producto_id:
                return producto
        return None

    def eliminar_producto(self, producto_id: str) -> bool:
        """Borra un producto por su id. Devuelve True si lo ha borrado."""
        producto = self.buscar_producto(producto_id)
        if producto is None:
            return False
        self.productos.remove(producto)
        return True

    def obtener_productos(self, skip: int = 0, limit: int = 10,
                          nombre: Optional[str] = None) -> List[Producto]:
        """Devuelve los productos del inventario, paginados con skip y limit.

        Si se pasa nombre, solo devuelve los productos cuyo nombre lo contiene
        (sin distinguir mayusculas y minusculas).
        """
        productos = self.productos
        if nombre:
            productos = [p for p in productos if nombre.lower() in p.nombre.lower()]
        return productos[skip:skip + limit]

    def listar_productos(self) -> None:
        """Imprime por consola todos los productos de la tienda."""
        print("---- PRODUCTOS DE LA TIENDA ----")
        if len(self.productos) == 0:
            print("No hay productos en el inventario")
        for producto in self.productos:
            print(producto)

    # ---------- PEDIDOS ----------

    def realizar_pedido(self, usuario_id: str,
                        productos_pedidos: List[Tuple[str, int]]) -> Pedido:
        """Crea un pedido si el usuario existe y hay stock de todo.

        productos_pedidos es una lista de tuplas (id_producto, cantidad).
        Si algo falla lanza una excepcion y no se toca el stock.
        """
        usuario = self.buscar_usuario(usuario_id)
        if usuario is None:
            raise NoEncontradoError(f"No existe ningun usuario con id {usuario_id}")

        if not isinstance(usuario, Cliente):
            raise DatosInvalidosError("Solo los clientes pueden hacer pedidos")

        if len(productos_pedidos) == 0:
            raise DatosInvalidosError("El pedido tiene que tener al menos un producto")

        # juntamos las cantidades por producto, por si el mismo producto
        # aparece en varias lineas (si no, se podria vender mas de lo que hay)
        cantidades: Dict[str, int] = {}
        for producto_id, cantidad in productos_pedidos:
            if cantidad <= 0:
                raise DatosInvalidosError("Las cantidades tienen que ser mayores que 0")
            cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad

        # primero comprobamos que existen y hay stock de todos los productos
        lineas: List[Tuple[Producto, int]] = []
        for producto_id, cantidad in cantidades.items():
            producto = self.buscar_producto(producto_id)
            if producto is None:
                raise NoEncontradoError(f"No existe ningun producto con id {producto_id}")
            if not producto.hay_stock(cantidad):
                raise ConflictoError(
                    f"No hay stock suficiente de {producto.nombre} "
                    f"(pedido: {cantidad}, disponible: {producto.stock})")
            lineas.append((producto, cantidad))

        # si todo esta bien, creamos el pedido y descontamos el stock
        pedido = Pedido(usuario, lineas)
        for producto, cantidad in lineas:
            producto.actualizar_stock(-cantidad)

        self.pedidos.append(pedido)
        return pedido

    def listar_pedidos_usuario(self, usuario_id: str) -> List[Pedido]:
        """Devuelve los pedidos de un usuario ordenados por fecha."""
        pedidos_usuario = []
        for pedido in self.pedidos:
            if pedido.cliente.id == usuario_id:
                pedidos_usuario.append(pedido)

        pedidos_usuario.sort(key=lambda pedido: pedido.fecha)
        return pedidos_usuario

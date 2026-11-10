"""Cliente de la API REST de la tienda online, hecho con requests.

Practica 2 (parte 2) - Marcos Laso Garcia

Este script NO importa nada del servidor (ni TiendaService ni los modelos):
todo se hace con peticiones HTTP a la API.

Uso:
    python cliente.py                          -> usa BASE_URL (localhost)
    python cliente.py http://192.168.1.34:8000 -> usa la API de otro equipo
"""

import sys
import uuid

import requests

# direccion de la API: cambiarla aqui o pasarla como argumento al ejecutar el script
BASE_URL = "http://localhost:8000"


def comprobar(respuesta: requests.Response, codigo_esperado: int, accion: str):
    """Comprueba el codigo HTTP de la respuesta y devuelve el JSON si todo ha ido bien.

    Si el codigo no es el esperado, muestra el error que devuelve la API y para el programa.
    """
    print(f"{respuesta.request.method} {respuesta.url} -> {respuesta.status_code}")

    if respuesta.status_code != codigo_esperado:
        try:
            detalle = respuesta.json().get("detail")
        except ValueError:
            detalle = respuesta.text
        print(f"ERROR al {accion}: se esperaba {codigo_esperado} y llego "
              f"{respuesta.status_code}. Detalle: {detalle}")
        sys.exit(1)

    return respuesta.json()


# ---------- USUARIOS ----------

def crear_usuario(nombre: str, email: str, direccion: str) -> dict:
    datos = {"nombre": nombre, "email": email, "tipo": "cliente", "direccion_postal": direccion}
    respuesta = requests.post(f"{BASE_URL}/usuarios", json=datos, timeout=5)
    usuario = comprobar(respuesta, 201, "crear el usuario")
    print(f"   Usuario creado: {usuario['nombre']} ({usuario['email']}) - id {usuario['id']}")
    return usuario


def listar_usuarios() -> list:
    respuesta = requests.get(f"{BASE_URL}/usuarios", params={"limit": 100}, timeout=5)
    usuarios = comprobar(respuesta, 200, "listar los usuarios")
    print(f"   Hay {len(usuarios)} usuario(s):")
    for usuario in usuarios:
        rol = "admin" if usuario["es_admin"] else "cliente"
        print(f"   - {usuario['nombre']} ({usuario['email']}) [{rol}]")
    return usuarios


# ---------- PRODUCTOS ----------

def crear_producto(datos: dict) -> dict:
    respuesta = requests.post(f"{BASE_URL}/productos", json=datos, timeout=5)
    producto = comprobar(respuesta, 201, "crear el producto")
    print(f"   Producto creado: {producto['nombre']} ({producto['tipo']}) - "
          f"{producto['precio']} EUR - stock {producto['stock']}")
    return producto


def listar_productos() -> list:
    respuesta = requests.get(f"{BASE_URL}/productos", params={"limit": 100}, timeout=5)
    productos = comprobar(respuesta, 200, "listar los productos")
    print(f"   Hay {len(productos)} producto(s):")
    for producto in productos:
        extra = ""
        if producto["tipo"] == "electronico":
            extra = f" - garantia {producto['meses_garantia']} meses"
        elif producto["tipo"] == "ropa":
            extra = f" - talla {producto['talla']}, color {producto['color']}"
        print(f"   - {producto['nombre']} ({producto['tipo']}): {producto['precio']} EUR, "
              f"stock {producto['stock']}{extra}")
    return productos


# ---------- PEDIDOS ----------

def crear_pedido(cliente_id: str, lineas: list) -> dict:
    """lineas es una lista de tuplas (producto_id, cantidad)."""
    datos = {
        "cliente_id": cliente_id,
        "items": [{"producto_id": producto_id, "cantidad": cantidad}
                  for producto_id, cantidad in lineas],
    }
    respuesta = requests.post(f"{BASE_URL}/pedidos", json=datos, timeout=5)
    pedido = comprobar(respuesta, 201, "crear el pedido")
    print(f"   Pedido creado: {pedido['id']} - total {pedido['total']} EUR")
    return pedido


def listar_pedidos_usuario(usuario_id: str) -> list:
    respuesta = requests.get(f"{BASE_URL}/usuarios/{usuario_id}/pedidos", timeout=5)
    pedidos = comprobar(respuesta, 200, "consultar los pedidos del usuario")
    print(f"   El usuario tiene {len(pedidos)} pedido(s):")
    for pedido in pedidos:
        print(f"   - Pedido {pedido['id'][:8]} del {pedido['fecha'][:19]} - total {pedido['total']} EUR")
        for item in pedido["items"]:
            print(f"       {item['nombre']} x{item['cantidad']} = {item['subtotal']} EUR")
    return pedidos


def main():
    global BASE_URL
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1].rstrip("/")

    print(f"Usando la API en {BASE_URL}\n")

    try:
        # sufijo para que el email no se repita si se ejecuta el script varias veces
        sufijo = uuid.uuid4().hex[:6]

        print("1. Crear un usuario")
        usuario = crear_usuario("Hermindo Ozores", f"hermindo{sufijo}@mail.com",
                                "Calle Mayor 1, Madrid")

        print("\n2. Consultar la lista de usuarios")
        listar_usuarios()

        print("\n3. Crear productos")
        movil = crear_producto({"tipo": "electronico", "nombre": "Movil Samsung",
                                "precio": 400.0, "stock": 10, "meses_garantia": 12})
        camiseta = crear_producto({"tipo": "ropa", "nombre": "Camiseta basica",
                                   "precio": 15.0, "stock": 20, "talla": "M", "color": "Negro"})
        crear_producto({"tipo": "generico", "nombre": "Taza", "precio": 5.5, "stock": 30})

        print("\n4. Consultar la lista de productos")
        listar_productos()

        print("\n5. Crear un pedido para el usuario")
        crear_pedido(usuario["id"], [(movil["id"], 1), (camiseta["id"], 2)])

        print("\n6. Consultar los pedidos del usuario")
        listar_pedidos_usuario(usuario["id"])

        print("\n7. Consultar los productos otra vez (el stock ha bajado)")
        listar_productos()

    except requests.exceptions.ConnectionError:
        print(f"\nERROR: no se puede conectar con la API en {BASE_URL}. "
              "Comprueba que el servidor esta arrancado y que la direccion es correcta.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"\nERROR: la API en {BASE_URL} no responde.")
        sys.exit(1)


if __name__ == "__main__":
    main()

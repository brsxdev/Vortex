from flask import Flask,jsonify,request,render_template
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
import mysql.connector as conector 
load_dotenv()
cloudinary.config(
    cloud_name=os.getenv("CLOUDI_NAME"),
    api_key=os.getenv("CLOUDI_API_KEY"),
    api_secret=os.getenv("CLOUDI_API_SECRET")
)
def obtener_conexion():
    return conector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="vortex",
        use_pure=True,
        connection_timeout=10
    )

app = Flask(__name__)
num = os.getenv("NUMERO_TELEFONO")
@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/busqueda")
def busqueda():
    return render_template("buscar.html")

@app.route("/carrito")
def carrito():
    return render_template("carrito.html")

@app.route("/obtenercategorias",methods=["POST"])
def entregarcategorias():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    try:
        ejecutador.execute("SELECT * FROM lista_categorias")
        rptacategorias = ejecutador.fetchall()
        if len(rptacategorias) > 0:
            return jsonify(rptacategorias)
        else:
            return jsonify({"exito":False})
    finally:
        ejecutador.close()
        conexion.close()

@app.route("/catalogoproductos",methods=["POST"])
def entregarcatalogo():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    try:
       ejecutador.execute("SELECT * FROM productos_vortex ORDER BY RAND() LIMIT 12")
       rpta = ejecutador.fetchall()
       if len(rpta) > 0:
            return jsonify(rpta)
       else:
            return jsonify({"exito":False})
    finally:
        ejecutador.close()
        conexion.close()

@app.route("/obtener-busqueda",methods=["POST"])
def entregarbusqueda():
    diccionario = request.get_json()
    categoria = diccionario["categoria"]
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    try:
        if categoria == "todo":
            ejecutador.execute("SELECT * FROM productos_vortex WHERE nombre LIKE %s LIMIT 20",(f"%{diccionario["dato"]}%",))
        else:
            ejecutador.execute("SELECT * FROM productos_vortex WHERE nombre LIKE %s AND categoria=%s LIMIT 20",(f"%{diccionario["dato"]}%",categoria))
        lista_tuplas = ejecutador.fetchall()
        if len(lista_tuplas) > 0:
            return jsonify({"exito":True,"lista":lista_tuplas})
        else:
            return jsonify({"exito":False})
    finally:
        ejecutador.close()
        conexion.close()
        
@app.route("/productos-pedidos",methods=["POST"])
def pedidos():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    diccionario = request.get_json()
    lista_productos = diccionario["lista_productos"]
    lista_verificados = []
    try:
        if len(lista_productos) > 0:
            for elemento in lista_productos:
                ejecutador.execute("SELECT * FROM productos_vortex WHERE id=%s",(elemento["id"],))
                lista_tuplas = ejecutador.fetchall()
                if len(lista_tuplas) > 0:
                    lista_verificados.append(lista_tuplas[0])
            
            return jsonify({"exito":True,"Lista":lista_verificados,"numero":num})
    finally:
        ejecutador.close()
        conexion.close()

@app.route("/añadir-producto",methods=["POST"])
def rptaañadir():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    nombre = request.form["nombre"]
    dscrp = request.form["descripcion"]
    precio = request.form["precio"]
    img = request.files["imagen"]
    stock = request.form["stock"]
    categoria = request.form["categoria"]
    resultado_imagen = cloudinary.uploader.upload(img, upload_preset="productos")
    url_imagen = resultado_imagen["secure_url"]
    try:
       ejecutador.execute("SELECT * FROM productos_vortex WHERE nombre=%s",(nombre,))
       tupla = ejecutador.fetchall()
       if len(tupla) > 0:
            return jsonify({"exito":False})
       else:
            ejecutador.execute("INSERT INTO productos_vortex(nombre,descripcion,imagen,stock,categoria,precio) VALUES(%s,%s,%s,%s,%s,%s)",(nombre,dscrp,url_imagen,stock,categoria,precio))
            ejecutador.execute("INSERT IGNORE INTO lista_categorias(categoria) VALUES(%s)",(categoria,))
            conexion.commit()
            return jsonify({"exito":True})
    finally:
        ejecutador.close()
        conexion.close()
        
@app.route("/actualizar-producto",methods=["PUT"])
def rptactualizar():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    campo = request.form["campo"]
    producto = request.form["producto"]
    try:
        ejecutador.execute("SELECT * FROM productos_vortex WHERE nombre=%s",(producto,))
        tupla = ejecutador.fetchall()
        if len(tupla) == 0:
            print("No existe el producto")
            return jsonify({"exito":False})
        else:
             if campo == "imagen":
                    contenido = request.form[campo]
                    rpta_imagen = cloudinary.uploader.upload(contenido, upload_preset="productos")
                    url_imagen = rpta_imagen["secure_url"]
                    ejecutador.execute(f"UPDATE productos_vortex SET `{campo}` = %s WHERE nombre=%s",(url_imagen,producto))
                    conexion.commit()
                    return jsonify({"exito":True})
             elif campo == "nombre":
                    contenido = request.form[campo]
                    ejecutador.execute(f"SELECT * FROM productos_vortex WHERE nombre=%s",(contenido,))
                    tuplanueva = ejecutador.fetchall()
                    if len(tuplanueva) > 0:
                        return jsonify({"exito":False})
                    else:
                        print("Es diferente")
                        ejecutador.execute(f"UPDATE productos_vortex SET `{campo}` = %s WHERE nombre=%s",(contenido,producto))
                        conexion.commit()
                        return jsonify({"exito":True})
             else:
                    contenido = request.form[campo]
                    ejecutador.execute(f"UPDATE productos_vortex SET `{campo}` = %s WHERE nombre=%s",(contenido,producto))
                    conexion.commit()
                    return jsonify({"exito":True})
    finally:
        ejecutador.close()
        conexion.close()
        
@app.route("/eliminar-producto",methods=["DELETE"])
def rptaeliminar():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    diccionario = request.get_json()
    id = int(diccionario["id"])
    
    try:
        ejecutador.execute("DELETE FROM productos_vortex WHERE id=%s",(id,))
    except:
        conexion.rollback()
        return jsonify({"exito":False})
    else:
        if ejecutador.rowcount > 0:
           conexion.commit()
           return jsonify({"exito": True})
        else:
           conexion.rollback()
           return jsonify({"exito": False})
    finally:
        ejecutador.close()
        conexion.close()
        
@app.route("/obtener-numero-productos",methods=["POST"])
def darnumero():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    
    try:
        ejecutador.execute("SELECT COUNT(*) AS TOTAL FROM productos_vortex")
        tupla_total = ejecutador.fetchone()
        if tupla_total is not None:
            ejecutador.execute("SELECT * FROM productos_vortex LIMIT 20")
            tupla_productos = ejecutador.fetchall()
            conexion.commit()
            return jsonify({"tupla_total":tupla_total,"tupla_productos":tupla_productos, "exito":True})
        else:
            conexion.commit()
            return jsonify({"exito":False})
    finally:
        ejecutador.close()
        conexion.close()
        
@app.route("/obtener-por-pagina",methods=["POST"])
def entregarporpagina():
    conexion = obtener_conexion()
    ejecutador = conexion.cursor()
    diccionario = request.get_json()
    dato = int(diccionario["dato"])
    try:
        ejecutador.execute("SELECT * FROM productos_vortex LIMIT 20 OFFSET %s",((dato-1)*20,))
        tupla = ejecutador.fetchall()
        if len(tupla) > 0:
            print(f"EXITO, tupla: {tupla}")
            return jsonify({"exito":True, "tupla":tupla})
        else:
            return jsonify({"exito":False})
    finally:
            ejecutador.close()
            conexion.close()
if __name__ == "__main__":
    app.run(debug=False)
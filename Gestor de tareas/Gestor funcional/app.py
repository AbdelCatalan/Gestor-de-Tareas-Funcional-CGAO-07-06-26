from flask import Flask, request, redirect, session, render_template_string
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "clave_secreta"

client = MongoClient("mongodb://localhost:27017/")
db = client["nutriapp"]

usuarios = db["usuarios"]
tareas = db["tareas"]

usuarios.create_index("email", unique=True)

index_html = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Inicio</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">NutriApp</a>

    <div class="dropdown ms-auto">
      <button class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
        Cuenta
      </button>

      <ul class="dropdown-menu dropdown-menu-end">
        {% if usuario %}
          <li><span class="dropdown-item-text">Hola {{usuario}}</span></li>
          <li><a class="dropdown-item" href="/tareas">Ir a tareas</a></li>
          <li><a class="dropdown-item text-danger" href="/logout">Cerrar sesion</a></li>
        {% else %}
          <li><a class="dropdown-item" href="/login">Iniciar sesion</a></li>
          <li><a class="dropdown-item" href="/registro">Registrarse</a></li>
        {% endif %}
      </ul>
    </div>

  </div>
</nav>

<div class="container mt-5 text-center">
    <h1 class="mb-3">Bienvenido a NutriApp</h1>
    <p>Usa el menu de arriba para navegar</p>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

login_html = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center" style="height:100vh;">

<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-4">
            <div class="card shadow p-4">

                <h3 class="text-center mb-3">Iniciar Sesion</h3>

                <form method="POST">
                    <input name="email" type="email" class="form-control mb-3" placeholder="Email" required>
                    <input name="password" type="password" class="form-control mb-3" placeholder="Contraseña" required>

                    <button class="btn btn-primary w-100">Entrar</button>
                </form>

                <p class="text-danger text-center mt-2">{{error}}</p>

                <div class="text-center mt-3">
                    <a href="/registro">Crear cuenta</a><br>
                    <a href="/">Volver</a>
                </div>

            </div>
        </div>
    </div>
</div>

</body>
</html>
"""

registro_html = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Registro</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center" style="height:100vh;">

<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-4">
            <div class="card shadow p-4">

                <h3 class="text-center mb-3">Registro</h3>

                <form method="POST">
                    <input name="nombre" class="form-control mb-3" placeholder="Nombre" required>
                    <input name="email" type="email" class="form-control mb-3" placeholder="Email" required>
                    <input name="password" type="password" class="form-control mb-3" placeholder="Contraseña" required>

                    <button class="btn btn-success w-100">Registrarse</button>
                </form>

                <p class="text-danger text-center mt-2">{{error}}</p>

                <div class="text-center mt-3">
                    <a href="/login">Ya tengo cuenta</a><br>
                    <a href="/">Volver</a>
                </div>

            </div>
        </div>
    </div>
</div>

</body>
</html>
"""

tareas_html = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Tareas</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">NutriApp</a>

    <div class="ms-auto">
        <a href="/logout" class="btn btn-danger">Cerrar sesion</a>
    </div>
  </div>
</nav>

<div class="container mt-5">
    <div class="card shadow p-4">

        <h2 class="text-center mb-4">Gestor de Tareas</h2>

        <form method="POST" action="/agregar_tarea">
            <div class="input-group mb-4">
                <input 
                    type="text" 
                    name="tarea"
                    class="form-control"
                    placeholder="Escribe una tarea..."
                    required
                >

                <button class="btn btn-primary">
                    Agregar
                </button>
            </div>
        </form>

        <ul class="list-group">

            {% for tarea in tareas %}

            <li class="list-group-item d-flex justify-content-between align-items-center">

                {{tarea["texto"]}}

                <div>
                    {% if not tarea["completada"] %}
                    <a href="/completar/{{tarea['_id']}}" class="btn btn-success btn-sm">
                        Completar
                    </a>
                    {% endif %}

                    <a href="/eliminar/{{tarea['_id']}}" class="btn btn-danger btn-sm">
                        Eliminar
                    </a>
                </div>

            </li>

            {% else %}

            <li class="list-group-item text-center">
                No hay tareas
            </li>

            {% endfor %}

        </ul>

    </div>
</div>

</body>
</html>
"""

@app.route("/")
def inicio():
    return render_template_string(
        index_html,
        usuario=session.get("usuario")
    )

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        try:

            usuarios.insert_one({
                "nombre": request.form["nombre"],
                "email": request.form["email"],
                "password": request.form["password"]
            })

            return redirect("/login")

        except DuplicateKeyError:

            return render_template_string(
                registro_html,
                error="El email ya existe"
            )

    return render_template_string(
        registro_html,
        error=""
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = usuarios.find_one({
            "email": request.form["email"],
            "password": request.form["password"]
        })

        if usuario:

            session["usuario"] = usuario["email"]

            return redirect("/tareas")

        else:

            return render_template_string(
                login_html,
                error="Datos incorrectos"
            )

    return render_template_string(
        login_html,
        error=""
    )

@app.route("/tareas")
def gestor_tareas():

    if "usuario" not in session:
        return redirect("/login")

    lista_tareas = list(
        tareas.find({
            "usuario": session["usuario"]
        })
    )

    return render_template_string(
        tareas_html,
        tareas=lista_tareas
    )

@app.route("/agregar_tarea", methods=["POST"])
def agregar_tarea():

    if "usuario" not in session:
        return redirect("/login")

    tareas.insert_one({
        "texto": request.form["tarea"],
        "completada": False,
        "usuario": session["usuario"]
    })

    return redirect("/tareas")

@app.route("/completar/<id>")
def completar_tarea(id):

    if "usuario" not in session:
        return redirect("/login")

    tareas.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "completada": True
            }
        }
    )

    return redirect("/tareas")

@app.route("/eliminar/<id>")
def eliminar_tarea(id):

    if "usuario" not in session:
        return redirect("/login")

    tareas.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/tareas")

@app.route("/logout")
def logout():

    session.pop("usuario", None)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
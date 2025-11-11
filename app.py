from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_segura_2025'

# Configurar base de datos
DATABASE = 'taxi_app.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Crear tablas si no existen"""
    if not os.path.exists(DATABASE):
        db = get_db()
        cursor = db.cursor()
        
        # Tabla de usuarios (pasajeros)
        cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefono TEXT,
                clave TEXT NOT NULL,
                tipo TEXT DEFAULT 'pasajero',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de viajes (ACTUALIZADA)
        cursor.execute('''
            CREATE TABLE viajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                nombre_cliente TEXT NOT NULL,
                email_cliente TEXT,
                telefono_cliente TEXT,
                origen TEXT NOT NULL,
                destino TEXT NOT NULL,
                tipo TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                motivo_cancelacion TEXT,
                observaciones TEXT,
                fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        ''')
        
        # Tabla de conductores
        cursor.execute('''
            CREATE TABLE conductores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefono TEXT NOT NULL,
                clave TEXT NOT NULL,
                placa_vehiculo TEXT NOT NULL,
                disponible INTEGER DEFAULT 1,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        db.commit()
        db.close()

# Inicializar BD al arrancar
init_db()

# ==================== RUTAS PÚBLICAS ====================

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

# ==================== REGISTRO ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        clave = request.form.get('clave')
        clave_confirm = request.form.get('clave_confirm')
        
        # Validaciones
        if not nombre or not email or not clave:
            error = "Todos los campos son obligatorios"
        elif clave != clave_confirm:
            error = "Las contraseñas no coinciden"
        elif len(clave) < 6:
            error = "La contraseña debe tener al menos 6 caracteres"
        else:
            db = get_db()
            cursor = db.cursor()
            try:
                # Hash de la contraseña
                clave_hash = generate_password_hash(clave)
                cursor.execute('''
                    INSERT INTO usuarios (nombre, email, telefono, clave, tipo)
                    VALUES (?, ?, ?, ?, 'pasajero')
                ''', (nombre, email, telefono, clave_hash))
                db.commit()
                db.close()
                return redirect('/login?msg=Registro exitoso. Inicia sesión')
            except sqlite3.IntegrityError:
                error = "El email ya está registrado"
                db.close()
    
    return render_template('register.html', error=error)

# ==================== LOGIN PASAJERO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = request.args.get('msg')
    if request.method == 'POST':
        email = request.form.get('email')
        clave = request.form.get('clave')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        usuario = cursor.fetchone()
        db.close()
        
        if usuario and check_password_hash(usuario['clave'], clave):
            session['usuario_id'] = usuario['id']
            session['usuario_nombre'] = usuario['nombre']
            session['usuario_email'] = usuario['email']
            session['usuario_telefono'] = usuario['telefono']
            return redirect('/panel_usuario')
        else:
            error = "Email o contraseña incorrectos"
    
    return render_template('login.html', error=error)

# ==================== PANEL DE USUARIO ====================

@app.route('/panel_usuario')
def panel_usuario():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
    usuario = cursor.fetchone()
    db.close()
    
    return render_template('panel_usuario.html', usuario=usuario)

# ==================== LOGOUT ====================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/salir')
def salir():
    session.clear()
    return redirect('/')

# ==================== SOLICITAR VIAJE (ACTUALIZADO) ====================

@app.route('/solicitar_viaje', methods=['GET', 'POST'])
def solicitar_viaje():
    if request.method == 'POST':
        origen = request.form.get('origen')
        destino = request.form.get('destino')
        tipo = request.form.get('tipo')
        observaciones = request.form.get('observaciones', '')
        
        usuario_id = session.get('usuario_id', 1)
        nombre_cliente = session.get('usuario_nombre', 'Cliente Anónimo')
        email_cliente = session.get('usuario_email', '')
        telefono_cliente = session.get('usuario_telefono', '')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO viajes 
            (usuario_id, nombre_cliente, email_cliente, telefono_cliente, 
             origen, destino, tipo, estado, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?)
        ''', (usuario_id, nombre_cliente, email_cliente, telefono_cliente, 
              origen, destino, tipo, observaciones))
        db.commit()
        db.close()
        
        return redirect('/viajes?msg=Viaje solicitado exitosamente')
    
    return render_template('solicitar_viaje.html')

# ==================== MIS VIAJES (ACTUALIZADO) ====================

@app.route('/viajes', methods=['GET', 'POST'])
def viajes():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    # Si es POST y viene con motivo de cancelación
    if request.method == 'POST':
        viaje_id = request.form.get('viaje_id')
        motivo = request.form.get('motivo_cancelacion')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            UPDATE viajes 
            SET estado = 'cancelado', motivo_cancelacion = ?
            WHERE id = ? AND usuario_id = ?
        ''', (motivo, viaje_id, session['usuario_id']))
        db.commit()
        db.close()
        
        return redirect('/viajes?msg=Viaje cancelado')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM viajes WHERE usuario_id = ? ORDER BY fecha_solicitud DESC', 
                   (session['usuario_id'],))
    mis_viajes = cursor.fetchall()
    db.close()
    
    msg = request.args.get('msg')
    return render_template('viajes.html', viajes=mis_viajes, msg=msg)

# ==================== VER SEGUIMIENTO ====================

@app.route('/seguimiento')
def seguimiento():
    return render_template('seguimiento.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/map_seguimiento')
def map_seguimiento():
    return render_template('map_seguimiento.html')

# ==================== OTROS ====================

@app.route('/pedir', methods=['GET', 'POST'])
def pedir():
    if request.method == 'POST':
        pass
    return render_template('pedir.html')

@app.route('/ride')
def ride():
    return render_template('ride.html')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/layout')
def layout():
    return render_template('layout.html')

@app.route('/logout_old')
def logout_old():
    session.clear()
    return render_template('logout.html')

@app.route('/registro_conductor', methods=['GET', 'POST'])
def registro_conductor():
    if request.method == 'POST':
        pass
    return render_template('registro_conductor.html')

@app.route('/inscribir_conductor', methods=['GET', 'POST'])
def inscribir_conductor():
    if request.method == 'POST':
        pass
    return render_template('inscribir_conductor.html')

@app.route('/registro_pt', methods=['GET', 'POST'])
def registro_pt():
    if request.method == 'POST':
        pass
    return render_template('registro_pt.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        pass
    return render_template('registro.html')

# ==================== ADMIN ====================

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario == "admin_app" and clave == "adminsecreta":
            session['admin'] = usuario
            return redirect('/admin_panel')
        else:
            error = "Datos incorrectos de admin"
    return render_template('admin_login.html', error=error)

@app.route('/admin_panel')
def admin_panel():
    if 'admin' not in session:
        return redirect('/admin_login')
    return render_template('admin_panel.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

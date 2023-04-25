from flask import Flask, request, jsonify, make_response, render_template
from flask_sqlalchemy import SQLAlchemy
import uuid # for public id
from werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, render_template, make_response
from werkzeug.security import generate_password_hash
import uuid
import re

# creates Flask object
app = Flask(__name__)
# configuration
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# INSTEAD CREATE A .env FILE AND STORE IN IT
app.config['SECRET_KEY'] = 'Apoco_si_pa'
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game_search.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# creates SQLALCHEMY object
db = SQLAlchemy(app)

# Database ORMs
class user_login(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(90))  # Asegúrate de que la indentación sea igual que las líneas anteriores
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))

with app.app_context():
    db.create_all()

# decorator for verifying the JWT
def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None
		# jwt is passed in the request header
		if 'x-access-token' in request.headers:
			token = request.headers['x-access-token']
		# return 401 if token is not passed
		if not token:
			return jsonify({'message' : 'Token is missing !!'}), 401

		try:
			# decoding the payload to fetch the stored details
			print(token)
			print(app.config['SECRET_KEY'])
			data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

			current_user = user_login.query\
				.filter_by(public_id = data['public_id'])\
				.first()
		except:
			return jsonify({
				'message' : 'Token is invalid !!'
			}), 401
		# returns the current logged in users context to the routes
		return f(current_user, *args, **kwargs)

	return decorated



# User Database Route
# this route sends back list of users
@app.route('/user', methods =['GET'])
@token_required
def get_all_users(current_user):
	# querying the database
	# for all the entries in it
	users = user_login.query.all()
	# converting the query objects
	# to list of jsons
	output = []
	for user in users:
		# appending the user data json
		# to the response list
		output.append({
			'id': user.id,
			'name' : user.name,
			'email' : user.email
		})

	return jsonify({'users': output})

# route for logging user in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # obtiene los datos del formulario
        auth = request.form

        if not auth or not auth.get('username') or not auth.get('password'):
            # devuelve 401 si falta algún correo electrónico o contraseña
            return make_response(
                'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
            )

        user = user_login.query.filter_by(username=auth.get('username')).first()

        if not user:
            # devuelve 401 si el usuario no existe
            return make_response(
                'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
            )

        if check_password_hash(user.password, auth.get('password')):
            # genera el token de autenticación JWT
            token = jwt.encode(
                {
                    'public_id': user.public_id,
                    'exp': datetime.utcnow() + timedelta(hours=1)  # tiempo de expiración del token
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            # devuelve la respuesta con el token en el encabezado
            return jsonify({'token': token})

        # devuelve 401 si la contraseña es incorrecta
        return make_response(
            'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
        )

    # renderiza el formulario de inicio de sesión
    return render_template('login2.html')

# signup route
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        # crea un diccionario con los datos del formulario
        data = request.form

        # obtiene nombre, correo electrónico y contraseña
        name = data.get('name')
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # verifica el formato de correo electrónico
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return make_response('Invalid email format.', 400)

        # verifica si el usuario ya existe en la base de datos
        user = user_login.query.filter_by(email=email).first()
        if not user:
            # crea un nuevo objeto ORM de usuario
            user = user_login(
                public_id=str(uuid.uuid4()),
                name=name,
                username=username,
                email=email,
                password=generate_password_hash(password)
            )
            # inserta el usuario en la base de datos
            db.session.add(user)
            db.session.commit()

            return make_response('Successfully registered.', 201)
        else:
            # devuelve un código 202 si el usuario ya existe
            return make_response('User already exists. Please Log in.', 202)
    else:
        # muestra la plantilla de registro
        return render_template('signup2.html')
    
class games(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    release_date = db.Column(db.String(10))
    platform = db.Column(db.String(50))
    genre = db.Column(db.String(50))
    requeriments_id = db.Column(db.Integer)
    rating_id = db.Column(db.Integer)

# Cambia el nombre de la variable que almacena los resultados de la consulta a "games" (en minúscula y plural)
@app.route('/games', methods=['GET'])
def get_games():
    # consulta todos los registros en la tabla "games"
    games_list = games.query.all()  # Cambia el nombre de la variable
    # crea una lista para almacenar los datos de los juegos
    output = []
    # itera sobre los registros y agrega los campos solicitados a la lista de salida
    for game in games_list:  # Cambia el nombre de la variable
        game_data = {
            'name': game.name,
            'description': game.description,
            'release_date': game.release_date,
            'platform': game.platform,
            'genre': game.genre,
            'requeriments_id': game.requirements_id,
            'rating_id': game.rating_id
        }
        output.append(game_data)
    # devuelve la lista de juegos en formato JSON
    return jsonify({'games': output})

if __name__ == "__main__":
	# setting debug to True enables hot reload
	# and also provides a debugger shell
	# if you hit an error while running the server
	app.run(debug = True)
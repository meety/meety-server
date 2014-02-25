import os, json, base64
from flask import Flask, make_response, request
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from multiprocessing import Process, Manager
from xmpp_client import start_xmpp_client
from users import User

app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")
app.secret_key = os.urandom(24)

login_manager = LoginManager(app)

# HTTP Endpoints
# Communication to the server

@app.route('/')
def index():

	response = make_response(json.dumps({'message':'ok'}), 200)
	response.headers["Content-Type"] = "application/json"
	return response

@app.route('/commn')
def commn_status():

	commn_status = {
			'status' : commn['status'],
			'description' : commn['description']
	}

	response = make_response(json.dumps({'commn':commn_status}), 200)
	response.headers["Content-Type"] = "application/json"
	return response

@login_manager.user_loader
def load_user(username):
	return User.get(username)

@login_manager.unauthorized_handler
def unauthorized():
	response = make_response(json.dumps({'error':'unauthorized'}), 401)
	response.headers["Content-Type"] = "application/json"
	return response

@app.route('/register', methods=['POST'])
def register():

	try:
		data = request.json
		if ( data == None ):
			raise Exception()
	except:
		response = make_response(json.dumps({'register':'malformed'}), 400)
		response.headers["Content-Type"] = "application/json"
		return response
	else:
		data = dict(data)
		username = data.get('username', None)
		password = data.get('password', None)

	if ( username == None or password == None ):
		response = make_response(json.dumps({'register':'malformed'}), 400)
		response.headers["Content-Type"] = "application/json"
		return response

	elif ( User.get(username) != None ):
		response = make_response(json.dumps({'error':'username taken'}), 403)
		response.headers["Content-Type"] = "application/json"
		return response

	else:
		try:
			User(username, password)
			response = make_response(json.dumps({'register':'success'}), 200)
		except:
			response = make_response(json.dumps({'register':'fail'}), 500)
		response.headers["Content-Type"] = "application/json"
		return response

@app.route('/login', methods=['POST'])
def login():

	try:
		auth = request.headers['Authorization']	
		if auth.startswith("Basic "):
			auth = auth.replace("Basic ", "", 1).strip()
		auth = base64.b64decode(auth)
		username, password = auth.split(":")
	except:
		response = make_response(json.dumps({'error':'malformed'}),
							400)
		response.headers["Content-Type"] = "application/json"
		return response

	if User.auth(username, password):
		if login_user(User.get(username)):
			response = make_response(json.dumps({'login':'success'}), 200)
		else:
			response = make_response(json.dumps({'login':'fail'}), 500)
	else:
		response = make_response(json.dumps({'error':'unauthorized'}), 401)

	response.headers["Content-Type"] = "application/json"
	return response

@app.route('/logged', methods=['GET'])
def logged():

	json_response = {'status':'nobody is logged'}

	if current_user.is_authenticated():
		json_response['status'] = "%s is logged" % (current_user.uid)

	response = make_response(json.dumps(json_response), 200)
	response.headers["Content-Type"] = "application/json"
	return response
	
@app.route('/logout', methods=['POST'])
@login_required
def logout():
	if logout_user():
		response = make_response(json.dumps({'logout':'success'}), 200)
	else:
		response = make_response(json.dumps({'logout':'fail'}), 500)

	response.headers["Content-Type"] = "application/json"
	return response

if __name__ == "__main__":

	commn = Manager().dict()
	commn['status'] = 0
	commn['description'] = 'about to start'
	commn['server'] = app.config['SERVER']
	commn['port'] = app.config['PORT']
	commn['gcm_username'] = app.config['USERNAME']
	commn['gcm_password'] = app.config['PASSWORD']

	xmpp_client_process = Process(target=start_xmpp_client, args=(commn,))
	xmpp_client_process.daemon = True
	xmpp_client_process.start()

	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port)

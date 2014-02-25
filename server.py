import os, sys, json, xmpp, random, string, base64
from flask import Flask, make_response, request
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from multiprocessing import Process, Manager
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

	response = make_response(json.dumps({'commn':dict(commn)}), 200)
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

	data = request.json

	if ( data == None ):
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

# XMPP Client

def random_id():
	rid = ''
	for x in range(8):
		rid += random.choice(string.ascii_letters + string.digits)
	return rid

def start_xmpp_client(commn):

	def callback_function_I(session, message):

		global unacked_messages_quota

		gcm = message.getTags('gcm')

		if gcm:
			gcm_json = gcm[0].getData()
			msg = json.loads(gcm_json)
			if not msg_has_key('message_type'):
				#can send response back here
				send({'to': msg['from'],
					'message_type': 'ack',
					'message_id': msg['message_id']})
				if msg.has_key('from'):
					send_queue.append({
						'to': msg['from'],
						'message_id': random_id(),
						'data': {'pong': 1}
					})
			elif ( msg['message_type'] == 'ack' 
			or msg['message_type'] == 'nack'):
				unacked_messages_quota += 1

	def send(client, json_dict):

		template = (
		"""<message>
			<gcm xmlns='google:mobile:data'>
				{1}
			</gcm>
		</message>""")

		client.send(xmpp.protocol.
			Message(node=template.format(client.Bind.bound[0],
				json.dumps(json_dict))))

	def flush_queued_messages():

		global unacked_messages_quota

		while len(send_queue) and unacked_messages_quota > 0:
			send(send_queue.pop(0))
			unacked_messages_quota -= 1

	client = xmpp.Client(app.config['SERVER'], debug=['socket'])
	client.connect(server=(app.config['SERVER'],
				app.config['PORT']),
				secure=1, use_srv=False)
	auth = client.auth(app.config['USERNAME'],
				app.config['PASSWORD'])

	if not auth:
		commn['status'] = -1
		commn['description'] = 'xmpp client authentication failed'
		sys.exit(1)

	unacked_messages_quota = 1000
	send_queue = []

#	client.RegisterHandler('event1', callback_function)
#	client.RegisterHandler('event2', callback_function_2)
#	client.RegisterHandler('event3', callback_function_3)
#	...
	client.RegisterHandler('eventI', callback_function_I)
#	...
#	client.RegisterHandler('eventN', callback_function_N)

	commn['status'] = 1
	commn['description'] = 'xmpp client running'

	while True:
		client.Process(1)
		flush_queued_messages()


if __name__ == "__main__":

	commn = Manager().dict()
	commn['status'] = 0
	commn['description'] = 'about to start'

	xmpp_client_process = Process(target=start_xmpp_client, args=(commn,))
	xmpp_client_process.daemon = True
	xmpp_client_process.start()

	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port)

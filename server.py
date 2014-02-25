import os, sys, json, xmpp, random, string
from flask import Flask, make_response
from multiprocessing import Process, Manager

server = Flask(__name__)
server.config.from_object("config.DevelopmentConfig")

# HTTP Endpoints
# Communication to the server

@server.route('/')
def index():

	response = make_response(json.dumps({'message':'ok'}), 200)
	response.headers["Content-Type"] = "application/json"
	return response

@server.route('/commn')
def commn_status():

	response = make_response(json.dumps({'commn':dict(commn)}), 200)
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

	client = xmpp.Client(server.config['SERVER'], debug=['socket'])
	client.connect(server=(server.config['SERVER'],
				server.config['PORT']),
				secure=1, use_srv=False)
	auth = client.auth(server.config['USERNAME'],
				server.config['PASSWORD'])

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
	server.run(host="0.0.0.0", port=port)

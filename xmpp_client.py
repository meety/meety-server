import sys, json, xmpp, random, string

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

	client = xmpp.Client(commn['server'], debug=['socket'])
	client.connect(server=(commn['server'],
				commn['port']),
				secure=1, use_srv=False)
	auth = client.auth(commn['gcm_username'],
				commn['gcm_password'])

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



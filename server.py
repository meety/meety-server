import os, sys, json, xmpp, random, string
from flask import Flask, make_response

server = Flask(__name__)
server.config.from_object("config.DevelopmentConfig")

@server.route('/')
def index():
	response = make_response(json.dumps({'message':'ok'}), 200)
	response.headers["Content-Type"] = "application/json"
	return response

if __name__ == "__main__":

	port = int(os.environ.get("PORT", 5000))
	server.run(host="0.0.0.0", port=port, debug=True)	

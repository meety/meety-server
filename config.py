class Config(object):
	SERVER = 'gcm.googleapis.com'
	PORT = 5235
	USERNAME = 'GCM SENDER ID'
	PASSWORD = 'API KEY'
	DEBUG = False

class ProductionConfig(Config):
	DEBUG = False

class DevelopmentConfig(Config):
	DEBUG = True

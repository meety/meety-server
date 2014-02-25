from flask.ext.login import UserMixin

class User(UserMixin):

	users = {}

	def __init__(self, username, password, active=True):
		self.uid = unicode(username)
		self.password = password
		self.active = active
		User.users[self.uid] = self
		print "REGISTERED: %s::%s" % (self.uid, self.password)

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.uid)

	@staticmethod
	def auth(uid, password):

		print "EXISTING USERS: ", User.users
		print "AUTH: %s::%s" % (uid, password)
		
		user = User.users.get(unicode(uid), None)
		if user != None and user.password == password:
			return True
		return False

	@staticmethod
	def get(uid):
		return User.users.get(unicode(uid), None)

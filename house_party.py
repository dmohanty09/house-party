from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask import escape
import soundcloud
import pdb
import requests
import json

import sqlite3
from flask import g
DATABASE = 'database.db'

app = Flask(__name__)
# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_users_feed(access_tokens):
	feeds = []
	for token in access_tokens:
		# create client object with access token
		#client = soundcloud.Client(access_token=token)
		# make an authenticated call
		#user_feed = client.get('/me/activities/tracks/affiliated')
		user_feed = requests.get('https://api.soundcloud.com/me/activities/tracks/affiliated',
								 params={'oauth_token': token}).json()
		print user_feed
		feeds.append(user_feed['collection'])
	return feeds

def merged_feed(feeds):
	#return list(sum(feeds, []))
	sorted_feed = sorted(sum(feeds, []), key=get_like_count)
	return map(lambda x: x['origin']['id'], sorted_feed)

def get_like_count(track):
	track['origin']['favoritings_count'].real

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def hello_world():
	if 'username' in session:
		users = []
		for user in query_db('select * from users'):
			uid = user[0].encode()
			access_token = user[1].encode()
			users.append(access_token)
			print uid, 'has the access_token', access_token
		feed = merged_feed(get_users_feed(users))
		#pdb.set_trace()
		#return 'Logged in as %s' % escape(session['username'])
		return render_template('index.html',username=escape(session['username']),oembed_feed=feed)
	# create client object with app credentials
	client = soundcloud.Client(client_id='2c4cd2f42c62536556e2d498c4993159',
                           	   client_secret='dfde246cb62560cdf14c4524d76d046f',
                           	   redirect_uri='http://localhost:5000/callback')
    # redirect user to authorize URL
	return redirect(client.authorize_url())

@app.route('/callback')
def callback():
	# create client object with app credentials
	client = soundcloud.Client(client_id='2c4cd2f42c62536556e2d498c4993159',
                           	   client_secret='dfde246cb62560cdf14c4524d76d046f',
                           	   redirect_uri='http://localhost:5000/callback')
	code = request.args.get('code')
	access_token = client.exchange_token(code)
	#return render_template('index.html')
	#return "Hi There, %s" % client.get('/me').username
	session['username'] = client.get('/me').username
	session['access_token'] = access_token.obj['access_token'].encode()

	db_args = (session['username'],session['access_token'],)
	query_db('insert into users (uid,access_token) values (?,?)', db_args)
	get_db().commit()
	return redirect('/')

@app.route('/oembed/track/<id>')
def oembed_track(id):
	url = 'http://api.soundcloud.com/tracks/%s' % id
	oembed = requests.get('http://soundcloud.com/oembed',
						  params={'format': 'json',
								  'url': url,
								  'client_id': '2c4cd2f42c62536556e2d498c4993159'}).json()
	return oembed['html']

if __name__ == '__main__':
    app.run(debug=True)

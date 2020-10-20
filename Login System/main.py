from flask import Flask, render_template, request, session, redirect, url_for
from DBcm import UseDatabase
import re
import hashlib

app=Flask(__name__)

dbconfig={'host': '127.0.0.1',
	'user': 'logindbuser',
	'password': 'ldbupwd',
	'database': 'logindb',}

app.secret_key="ThisIsPassword"

@app.route('/')
def entry() ->'html':
	if 'logged_in' in session:
		return redirect(url_for('home'))
	msg=""
	return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register() ->'html':
	msg=""
	if request.method=='POST' and 'user_name' in request.form and 'password' in request.form and 'email' in request.form:
		username=request.form['user_name']
		email=request.form['email']
		password=request.form['password']
		ip=request.remote_addr
		client=request.user_agent.browser
		salt="!.+^mk-3@"
		password+=salt
		password=hashlib.md5(password.encode())
		password=password.hexdigest()

		with UseDatabase(dbconfig) as cursor:
			cursor.execute('select * from account where email=%s', (email,))
			account=cursor.fetchone()
		if account:
			msg="This email is already registered!"
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg="Invalie email address!"
		elif not re.match("^[A-Za-z0-9]*$", username):
			msg="Username must contain only characters and numbers!"
		elif not username or not password or not email:
			msg="Please fill out the form!"
		else:
			with UseDatabase(dbconfig) as cursor:
				cursor.execute("insert into account values(NULL, %s, %s, %s)", (username, password, email))
				cursor.execute("select id from account where username=%s and email=%s", (username, email))
				parentID=cursor.fetchone()[0]
				cursor.execute("insert into browser_info values(NULL, %s, %s, %s)", (ip, client, parentID))
			msg="You have successfully registered"

	elif request.method=='POST':
		msg="Please fill the form"
	return render_template('register.html', msg=msg)


@app.route('/login', methods=['POST', 'GET'])
def login() ->'html':
	msg=""
	if request.method=='POST' and 'email' in request.form and 'password' in request.form:
		email=request.form['email']
		password=request.form['password']
		ip=request.remote_addr
		client=request.user_agent.browser
		salt="!.+^mk-3@"
		password+=salt
		password=hashlib.md5(password.encode())
		password=password.hexdigest()
		
		with UseDatabase(dbconfig) as cursor:
			cursor.execute('select * from account where email=%s and password=%s', (email, password))
			account=cursor.fetchone()

		if account:
			session['logged_in']=True
			session['id']=account[0]
			session['username']=account[1]
			parentID=account[0]
			with UseDatabase(dbconfig) as cursor:
				cursor.execute("insert into browser_info values(NULL, %s, %s, %s)", (ip, client, parentID))
			return redirect(url_for('home'))
		else:
			msg="Incorrect username/password"

	return render_template('login.html', msg=msg)

@app.route('/logout')
def logout() ->'html':
	if session:
		del session['logged_in']
		del session['id']
		del session['username']
		msg="successfully logged out"
		return render_template('login.html', msg=msg)
	else:
		return "Already logged out"

@app.route('/home')
def home() ->'html':
	if 'logged_in' in session:
		return render_template('home.html', the_title="home", username=session['username'])
	return redirect(url_for('login'))

@app.route('/profile')
def profile() ->'html':
	if 'logged_in' in session:
		with UseDatabase(dbconfig) as cursor:
			_SQL="select p.username, p.email, c.ip, c.client from account as p join browser_info as c on c.user_id=p.id where p.id=%s order by c.id desc limit 1"
			cursor.execute(_SQL, (session['id'],))
			account=cursor.fetchone()
		return render_template('profile.html', username=account[0],email=account[1], ip=account[2], client=account[3])
	return redirect(url_for('login'))

@app.route('/status')
def status() ->str:
	if session:
		return "Logged in"
	else:
		return "Logged out"

if __name__=='__main__':
	app.run(debug=True)
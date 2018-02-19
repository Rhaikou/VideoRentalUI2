#!/usr/bin/python
# -*- coding: utf-8 -*-

# Uudelleenkäytetty VT4:n koodia

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template, make_response
import sqlite3
import logging
import os
import simplejson as json
import datetime
import hashlib

logging.basicConfig(filename=os.path.abspath('../../web/flask.log'),level=logging.DEBUG)

app = Flask(__name__) 
app.debug = True

# Tietokantayhteyden avaaminen
def connect_db():
	try:
		con = sqlite3.connect(os.path.abspath('../../hidden/video'))
		con.row_factory = sqlite3.Row
		# Viite-eheydet käyttöön
		con.execute("PRAGMA foreign_keys = 1")
	except Exception as e:
		logging.debug("Kanta ei aukea")
		# sqliten antama virheilmoitus:
		logging.debug(str(e))
	return con
	
@app.route('/hae_vuokraukset')
def get_rentals():
	# Yhdistä kanta
	db = connect_db()
	try:
		# Kysytään vuokratut elokuvat ja otetaan ne talteen
		cursor = db.execute("""SELECT Elokuva.Nimi, Elokuva.Julkaisuvuosi, Elokuva.ElokuvaID FROM Elokuva
		ORDER BY Elokuva.Nimi, Elokuva.Julkaisuvuosi ASC
		""")
		movies = []
		for row in cursor.fetchall():
			movies.append( dict(name=row[0], year=row[1], id=row[2]) )
		
		# Kysytään vuokraukset ja yhdistetään ne elokuviin
		cursor = db.execute("""SELECT Jasen.Nimi, Vuokraus.VuokrausPVM,
		Vuokraus.PalautusPVM, Vuokraus.Maksettu, Elokuva.ElokuvaID, Jasen.JasenID FROM Jasen, Vuokraus, Elokuva
		WHERE Vuokraus.JasenID = Jasen.JasenID AND Vuokraus.ElokuvaID = Elokuva.ElokuvaID
		ORDER BY Vuokraus.VuokrausPVM, Vuokraus.PalautusPVM ASC
		""")
		rentals = []
		# Yhdistetään vuokraukset elokuviin
		for row in cursor.fetchall():
			rentals.append( dict(member_name=row[0], rental_date=row[1], return_date=row[2],
			paid=row[3], movie_id=row[4], member_id=row[5]) )
		for movie in movies:
			movie['rentals'] = []
			for rental in rentals:
				if rental['movie_id'] == movie['id']:
					movie['rentals'].append(rental)
	except Exception as e:
		logging.debug(str(e))
		movies = ""
	# Suljetaan yhteys kantaan
	db.close()
	# Palautetaan etusivu
	resp = make_response( render_template("vuokraukset.xml", movies=movies) )
	resp.charset = "UTF-8"
	resp.mimetype = "text/xml"
	return resp

@app.route('/hae_jasenet')	
def get_members():
	db = connect_db()
	members = []
	try:
		# Jäsenet
		cursor = db.execute("""SELECT Jasen.Nimi AS MemberName, Jasen.JasenID AS MemberID FROM Jasen ORDER BY Jasen.Nimi ASC""")
		for row in cursor.fetchall():
			members.append( dict(name=row['MemberName'], id=row['MemberID']) )
	except Exception as e:
		logging.debug(str(e))
		members = ""
	resp = make_response( json.dumps(members) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp
	
@app.route('/hae_elokuvat')	
def get_movies():
	db = connect_db()
	movies = []
	try:
		# Elokuvat
		cursor = db.execute("""SELECT Elokuva.Nimi AS MovieName, Elokuva.ElokuvaID AS MovieID, Elokuva.Julkaisuvuosi AS MovieYear FROM Elokuva ORDER BY Elokuva.Nimi, Elokuva.Julkaisuvuosi ASC""")
		for row in cursor.fetchall():
			movies.append( dict(name=row['MovieName'], year=row['MovieYear'], id=row['MovieId']) )
	except Exception as e:
		logging.debug(str(e))
		movies = ""
	resp = make_response( json.dumps(movies) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp
	
@app.route('/hae_genret')	
def get_gemres():
	db = connect_db()
	genres = []
	try:
		# Genret
		cursor = db.execute("""SELECT Tyypinnimi AS GenreName, LajityyppiID AS Id FROM Lajityyppi ORDER BY Tyypinnimi ASC""")
		for row in cursor.fetchall():
			genres.append( dict(name=row['GenreName'], id=row['Id']) )
	except Exception as e:
		logging.debug(str(e))
		genres = ""
	resp = make_response( json.dumps(genres) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp
	
@app.route('/lisaa_vuokraus', methods=['POST','GET'])
def add_rental():
	# Alustetaan virhekentät ja kentät
	err_messages = {'rental_date':'', 'return_date':'', 'paid':'', 'general':'', 'success':'1'}	
	fields = {"member":"","movie":"","rental_date":"","return_date":"","paid":""}
	errors = False
	if request.method == 'POST':
		# Kysytään lomakkeen tiedot
		for k in fields:
			try:
				fields[k] = request.form[k]
			except KeyError:
				logging.debug("Kenttien lukeminen epäonnistui")
			except Exception as e:
				logging.debug(str(e))
		#Tarkistetaan maksukenttä
		try:
			maksu = float(fields['paid'])
			if maksu < 0:
				errors = True
				err_messages['paid'] = u'Maksun pitää olla positiivinen luku!'
		except ValueError:
			errors = True
			err_messages['paid'] = u'Maksun pitää olla positiivinen luku!'
		# Tarkistetaan päivmäärät
		rental_date = ""
		return_date = ""
		try:
			rental_date = datetime.datetime.strptime(fields['rental_date'], '%Y-%m-%d')
		except ValueError:
			errors = True
			err_messages['rental_date'] = u'Päivämäärän pitää olla muotoa: vvvv-kk-pp.'
		try:
			if fields['return_date']:
				return_date = datetime.datetime.strptime(fields['return_date'], '%Y-%m-%d')
			else:
				fields['return_date'] = u'Palauttamatta'
		except ValueError:
			errors = True
			err_messages['return_date'] = u'Päivämäärän pitää olla muotoa: vvvv-kk-pp.'
		if (return_date and rental_date) and (return_date < rental_date):
			errors =  True
			err_messages['return_date'] = 'Palautus ei voi olla aikaisempi kuin vuokraus!'
		# Jos virheitä ei ole, tehdään muutokset kantaan
		if not errors:
			db = connect_db()
			try:
				cursor = db.execute("""INSERT INTO Vuokraus (JasenID, ElokuvaID, VuokrausPVM, PalautusPVM, Maksettu)
				VALUES (:member_id, :movie_id, :rental_date, :return_date, :paid)
				""", {"member_id":fields['member'], "movie_id":fields['movie'], "rental_date":fields['rental_date'], 
				"return_date":fields['return_date'], "paid":fields['paid']})
				db.commit()
			except Exception as e:
				err_messages['general'] = u'Lisääminen ei onnistunut, yrititkö lisätä vuokrauksen joka on jo olemassa?'
				logging.debug(str(e))
			db.close()
		else:
			err_messages['success'] = 0
	resp = make_response( json.dumps(err_messages) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp

@app.route('/muokkaa_vuokraus', methods=['POST','GET'])
def edit_rental():
	# Alustetaan virhekentät ja kentät
	err_messages = {'rental_date':'', 'return_date':'', 'paid':'', 'general':'', 'success':'1'}	
	fields = {"member":"","movie":"","rental_date":"","return_date":"","paid":""}
	errors = False
	if request.method == 'POST':
		# Kysytään lomakkeen tiedot
		for k in fields:
			try:
				fields[k] = request.form[k]
			except KeyError:
				logging.debug("Kenttien lukeminen epäonnistui")
			except Exception as e:
				logging.debug(str(e))
		try:
			o_member = request.form['o_member']
			o_movie = request.form['o_movie']
			o_date = request.form['o_date']
		except KeyError:
			logging.debug("Kenttien lukeminen epäonnistui")
		except Exception as e:
			logging.debug(str(e))
		#Tarkistetaan maksukenttä
		try:
			maksu = float(fields['paid'])
			if maksu < 0:
				errors = True
				err_messages['paid'] = u'Maksun pitää olla positiivinen luku!'
		except ValueError:
			errors = True
			err_messages['paid'] = u'Maksun pitää olla positiivinen luku!'
		# Tarkistetaan päivmäärät
		rental_date = ""
		return_date = ""
		try:
			rental_date = datetime.datetime.strptime(fields['rental_date'], '%Y-%m-%d')
		except ValueError:
			errors = True
			err_messages['rental_date'] = u'Päivämäärän pitää olla muotoa: vvvv-kk-pp.'
		try:
			if fields['return_date']:
				return_date = datetime.datetime.strptime(fields['return_date'], '%Y-%m-%d')
			else:
				fields['return_date'] = u'Palauttamatta'
		except ValueError:
			errors = True
			err_messages['return_date'] = u'Päivämäärän pitää olla muotoa: vvvv-kk-pp.'
		if (return_date and rental_date) and (return_date < rental_date):
			errors =  True
			err_messages['return_date'] = 'Palautus ei voi olla aikaisempi kuin vuokraus!'
		# Jos virheitä ei ole, tehdään muutokset kantaan
		if not errors:
			db = connect_db()
			try:
				cursor = db.execute("""UPDATE Vuokraus SET JasenID=:member_id, ElokuvaID=:movie_id,
				VuokrausPVM=:rental_date, PalautusPVM=:return_date, Maksettu=:paid
				WHERE JasenID =:o_member AND ElokuvaID =:o_movie AND VuokrausPVM =:o_date
				""", {"member_id":fields['member'], "movie_id":fields['movie'], "rental_date":fields['rental_date'], 
				"return_date":fields['return_date'], "paid":fields['paid'], 'o_member':o_member,
				'o_movie':o_movie, 'o_date':o_date})
				db.commit()
			except Exception as e:
				err_messages['success'] = 0
				err_messages['general'] = u'Muokkaaminen ei onnistunut, näillä tiedoilla on jo vuokraus.'
				logging.debug(str(e))
			db.close()
		else:
			err_messages['success'] = 0
	resp = make_response( json.dumps(err_messages) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp

@app.route('/kirjaudu', methods=['POST','GET'])
def login():
	try:
		username = request.form['username']
		password = request.form['password']
	except:
		username = ""
		password = ""
	err = {'user':"", 'pass':"", 'success':0}
	m = hashlib.sha512()
	key = # salausavain
	m.update(key)
	m.update(password)
	right_pass = # salattu salasana
	# Tarkistetaan annetiinko oikeat tiedot
	if username == # käyttäjätunnus
	 and m.digest() == right_pass:
		err['success'] = 1
		# Tarkistetaan oliko virhe käyttäjätunnuksessa
	if username != # käyttäjätunnus
	:
		err['user'] = u'Käyttäjätunnusta ei löytynyt'
		err['success'] = 0
	# Tarkistetaan oliko virhe salasanassa
	if username == # käyttäjätunnus 
	and m.digest() != right_pass:
		err['pass'] = u'Salasana oli väärä'
		err['success'] = 0
	resp = make_response( json.dumps(err) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp

@app.route('/poista_elokuva', methods=['POST','GET'])
def delete_movie():
	err = {'msg':"", 'success':1}
	try: 
		movie = request.form['movie']
	except:
		movie = ""
	db = connect_db()
	try:
		cursor = db.execute("""DELETE FROM Elokuva WHERE ElokuvaID = :movie
		""", {"movie":movie})
		db.commit()
	except Exception as e:
		err['success'] = 0
		err['msg'] = u'Poistaminen ei onnistunut, yrititkö poistaa vuokrattua elokuvaa?'
		logging.debug(str(e))
	db.close()
	resp = make_response( json.dumps(err) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp

@app.route('/lisaa_elokuva', methods=['POST','GET'])
def add_movie():
	err = {'msg':"", 'success':1}
	fields = {"name":"","year":"","price":"","review":"","genre":""}
	# Kysytään lomakkeen tiedot
	for k in fields:
		try:
			fields[k] = request.form[k]
		except KeyError:
			logging.debug("Kenttien lukeminen epäonnistui")
		except Exception as e:
			logging.debug(str(e))
	db = connect_db()
	try:
		cursor = db.execute("""INSERT INTO Elokuva (Nimi, Julkaisuvuosi, Vuokrahinta, Arvio, LajityyppiID)
		VALUES (:name, :year, :price, :review, :genre)
		""", {"name":fields['name'], "year":fields['year'], "price":fields['price'], 
		"review":fields['review'], "genre":fields['genre'] })
		db.commit()
	except Exception as e:
		err['success'] = 0
		err['msg'] = u'Lisääminen ei onnistunut. Tarkista tiedot ja yritä uudelleen.'
		logging.debug(str(e))
	db.close()
	resp = make_response( json.dumps(err) )
	resp.charset = "UTF-8"
	resp.mimetype = "application/json"
	return resp

@app.route('/anna_sisalto', methods=['POST','GET'])
def send_content():
	resp = make_response( render_template("content.xml") )
	resp.charset = "UTF-8"
	resp.mimetype = "text/xml"
	return resp

if __name__ == '__main__':
	app.debug = True
	app.run(debug=True)

from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, reqparse
import json
import os
import requests
import sys

app = Flask(__name__)
app.config.update(SECRET_KEY=os.urandom(24))
db = SQLAlchemy(app)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
parser = reqparse.RequestParser()

API_KEY = "9de13c4538217f87c06f2b1b2bfb27b2"    # OpenWeather API

# SQLAlchemy City class
class City(db.Model):
    __tablename__ = 'Cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


db.create_all()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        dict_with_weather_info = []
        # Preparamos un diccionario con todas las ciudades de la BD y las mostramos en cards
        for city in City.query.filter().all():
            dict_with_weather_info.append(get_city_info(city.id, city.name))
        return render_template('index.html', weather=dict_with_weather_info)
    else:   # id POST
        city_name = request.form['city_name'].upper()
        if not city_exists(city_name):  # Si no existe (o en blanco) la ciudad, nos quejamos
            flash("The city doesn't exist!")
            return redirect('/')
        else:
            if City.query.filter(City.name == city_name).first() is None:   # Si no existe en la BD => la añadimos
                new_city = City(name=city_name)
                new_city.save()
            else:
                flash("The city has already been added to the list!")
                return redirect('/')
        return redirect(url_for("index"))   # redirect and force to reload with new data


def get_city_info(id, city_name):
    r = requests.get(f" http://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&appid={API_KEY}")
    r_json = json.loads(r.text)
    temperature = r_json['main']['temp']
    timeShift = r_json['timezone'] / 3600
    time_of_day = get_time_of_day(timeShift)
    weather_state = r_json['weather'][0]['main']    # or 'description'
    return {'id': id, 'temp': round(temperature, 1), 'desc': weather_state, 'time': time_of_day, 'city_name': city_name}


def city_exists(city_name):
    r = requests.get(f" http://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&appid={API_KEY}")
    return r.status_code < 400


def get_time_of_day(timeShift):
    morning = time(6, 0, 0)
    nightfall = time(17, 0, 0)

    if '-' in str(timeShift):
        hour = datetime.utcnow() + timedelta(hours=timeShift)
    else:
        hour = datetime.utcnow() - timedelta(hours=timeShift)
    if morning < hour.time() < nightfall:
        return "day"
    elif hour.time() > nightfall or hour.time() < morning:
        return "night"
    else:
        return "evening-morning"


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    city.delete()
    return redirect('/')


@app.route('/login')
def login():
    abort(401)


@app.route('/profile')
def profile():
    return 'This is profile page'


@app.route('/login')
def log_in():
    return 'This is login page'


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()

from flask import Flask, render_template, request, redirect, url_for
from datetime import timedelta
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from threading import Thread
from os import getenv
import html

load_dotenv()

# IMPORT DES MODULES
from modules.api import *
from modules.curl import *
import modules.monitoring as monitoring

theaters = [Theater(data["node"]) for data in
            requests.get("https://www.allocine.fr/_/localization_city/Brest").json()["values"]["theaters"]]

theaters += [Theater(data["node"]) for data in requests.get("https://www.allocine.fr/_/localization_city/Landerneau").json()["values"]["theaters"]]

timezone = ZoneInfo(getenv("TIMEZONE"))

def getShowtimes(date):
    showtimes: list[Showtime] = []

    for theater in theaters:
        showtimes.extend(theater.getShowtimes(date))

    data = {}

    for showtime in showtimes:
        movie = showtime.movie
        theater = showtime.theater

        if showtime.movie.title not in data.keys():
            data[movie.title] = {
                "title": movie.title,
                "duree": movie.runtime,
                "genres": ", ".join(movie.genres),
                "casting": ", ".join(movie.cast),
                "realisateur": movie.director,
                "synopsis": html.unescape(movie.synopsis),
                "affiche": movie.affiche,
                "director": movie.director,
                "wantToSee": movie.wantToSee,
                "url": f"https://www.allocine.fr/film/fichefilm_gen_cfilm={movie.id}.html",
                "seances": {}
            }

        if theater.name not in data[movie.title]["seances"].keys():
            data[movie.title]["seances"][theater.name] = []

        data[movie.title]["seances"][theater.name].append(showtime.startsAt.strftime("%H:%M"))

    data = data.values()

    data = sorted(data, key=lambda x: x["wantToSee"], reverse=True)

    return data

showtimes = []
for i in range(0, 7):
    day_showtimes = getShowtimes(datetime.now(timezone) + timedelta(days=i))
    showtimes.append(day_showtimes)
    print(f"{len(day_showtimes)} séances récupéré {i + 1}/7!")


def translate_month(num: int) -> str:
    months = ["janv", "févr", "mars", "avr", "mai", "juin",
              "juil", "août", "sept", "oct", "nov", "déc"]
    return months[num - 1] if 1 <= num <= len(months) else "???"


def translate_day(weekday: int) -> str:
    days = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
    return days[weekday] if 0 <= weekday < len(days) else "???"


app = Flask(__name__)

@app.route('/healthcheck')
def healthcheck():
    return 'ok'

@app.route('/<int:day>')
def special_day(day:int):
    return redirect(url_for("home", delta=day))

@app.route('/')
def home():
    delta = request.args.get("delta", default=0, type=int)

    if delta > 6: delta = 6
    if delta < 0: delta = 0

    useragent = request.headers.get('User-Agent')
    Thread(target=monitoring.log, kwargs={
        'ip': request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr),
        'useragent': useragent,
        'day': delta
    }).start()

    if useragent.startswith("curl/"):
        day = datetime.now(timezone) + timedelta(delta)
        return handle_curl(showtimes[delta], f"{day.day} {translate_month(day.month)}")

    dates = []

    for i in range(0, 7):
        day = datetime.now(timezone) + timedelta(i)
        dates.append({
            "jour": translate_day(day.weekday()),
            "chiffre": day.day,
            "mois": translate_month(day.month),
            "choisi": i == delta,
            "index": i
        })

    return render_template('index.html',
                           films=showtimes[delta],
                           dates=dates,
                           JAWG_API_KEY=getenv("JAWG_API_KEY"))

if __name__ == '__main__':
    app.run(host=getenv("HOST"), port=getenv("PORT"))
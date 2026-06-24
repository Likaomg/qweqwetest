
from flask import Flask, render_template, request, redirect, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","change-me")
DB = os.path.join(os.path.dirname(__file__), "database.db")

def db(): return sqlite3.connect(DB)

def init_db():
    c=db()
    cur=c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS games(id INTEGER PRIMARY KEY, title TEXT, platform TEXT, year TEXT, description TEXT, rating TEXT, image TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS favorites(user_id INTEGER, game_id INTEGER)")
    if cur.execute("SELECT COUNT(*) FROM games").fetchone()[0]==0:
        games=[
            ("Crash Bandicoot","PS1","1996","Классический платформер, в котором сумчатый герой путешествует по красочным островам, преодолевая ловушки и побеждая врагов. Игра сочетает динамичный геймплей, секретные уровни и запоминающихся персонажей. Каждый этап предлагает новые испытания и бонусы. Отличная анимация и музыка сделали проект культовым. До сих пор считается одной из лучших игр жанра.","4.8","https://upload.wikimedia.org/wikipedia/en/4/44/Crash_Bandicoot_Cover.png"),
            ("Metal Gear Solid","PS1","1998","Знаменитый шпионский боевик, где успех зависит от скрытности, тактики и внимательности. Игроку предстоит проникать на охраняемые базы и раскрывать масштабный заговор. Игра впечатляет кинематографичной постановкой и харизматичными героями. Каждая миссия предлагает несколько способов прохождения. Это одна из самых влиятельных игр своего времени.","4.9","https://upload.wikimedia.org/wikipedia/en/3/33/Metal_Gear_Solid_cover_art.png"),
            ("Silent Hill","PS1","1999","Психологический хоррор с мрачной атмосферой и запутанным сюжетом. Игрок исследует окутанный туманом город, полный опасностей и загадок. Монстры отражают внутренние страхи персонажей. Музыка и звуковой дизайн усиливают напряжение. История оставляет простор для размышлений даже после финала.","4.7","https://upload.wikimedia.org/wikipedia/en/9/96/Silent_Hill_video_game_cover.png"),
            ("Sonic the Hedgehog","SEGA","1991","Легендарный платформер о самом быстром ежике в мире. Игрок мчится по ярким уровням, собирая кольца и побеждая роботов доктора Эггмана. Высокая скорость сочетается с исследованием секретных маршрутов. Узнаваемый стиль и музыка сделали игру визитной карточкой консоли. Она остается любимой классикой для многих игроков.","4.8","https://upload.wikimedia.org/wikipedia/en/b/ba/Sonic_the_Hedgehog_1_Genesis_box_art.jpg"),
        ]
        cur.executemany("INSERT INTO games(title,platform,year,description,rating,image) VALUES(?,?,?,?,?,?)",games)
    c.commit(); c.close()

@app.route("/")
def index():
    c=db()
    games=c.execute("SELECT * FROM games").fetchall()
    favs=[]
    if "uid" in session:
        favs=[x[0] for x in c.execute("SELECT game_id FROM favorites WHERE user_id=?", (session["uid"],)).fetchall()]
    c.close()
    return render_template("index.html",games=games,favs=favs)

@app.route("/game/<int:id>")
def game(id):
    c=db()
    game=c.execute("SELECT * FROM games WHERE id=?", (id,)).fetchone()
    c.close()
    
    if not game: abort(404)
    return render_template("game.html",game=game)

@app.route("/favorite/<int:id>")
def favorite(id):
    if "uid" not in session: return redirect("/login")
    c=db()
    if not c.execute("SELECT * FROM favorites WHERE user_id=? AND game_id=?", (session["uid"],id)).fetchone():
        c.execute("INSERT INTO favorites VALUES (?,?)",(session["uid"],id))
        c.commit()
    c.close()
    return redirect("/")

@app.route("/favorites")
def favorites():
    if "uid" not in session: return redirect("/login")
    c=db()
    games=c.execute("SELECT g.* FROM games g JOIN favorites f ON g.id=f.game_id WHERE f.user_id=?", (session["uid"],)).fetchall()
    c.close()
    return render_template("favorites.html",games=games)

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        c=db()
        try:
            c.execute("INSERT INTO users(username,password) VALUES (?,?)",(request.form["username"],generate_password_hash(request.form["password"])))
            c.commit()
        except sqlite3.IntegrityError:
            pass
        c.close()
        return redirect("/login")
    return render_template("auth.html",title="Регистрация",btn="Создать аккаунт")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        c=db()
        u=c.execute("SELECT * FROM users WHERE username=?",(request.form["username"],)).fetchone()
        ok=u and check_password_hash(u[2],request.form["password"])
        c.close()
        if ok:
            session["uid"]=u[0]
            return redirect("/")
    return render_template("auth.html",title="Вход",btn="Войти")

init_db()

if __name__=="__main__":
    app.run()


@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route('/favorite/remove/<int:gid>')
def remove_favorite(gid):
    if 'user_id' not in session: return redirect('/login')
    c=db();cur=c.cursor();cur.execute('DELETE FROM favorites WHERE user_id=? AND game_id=?',(session['user_id'],gid));c.commit();c.close()
    return redirect('/favorites')

import sqlite3
from sqlite3 import Error

from flask import Flask
from flask import abort
from flask import request

app = Flask(__name__)

path = "/Users/baileykoestel/Desktop/CSC/movie-reviews.db"

@app.route("/movies")
def get_all_movies():
    movies = []
    conn = None
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM movies")
        movie_rows = cursor.fetchall()

        for movie in movie_rows:
            movie_id = movie["id"]
            movie_info = {
                "id": movie["id"],
                "title": movie["title"],
                "year": movie["year"],
                "actors": []
            }

            cursor.execute("SELECT * FROM actorsInMovies WHERE movieId = ?", (movie_id,))
            link_rows = cursor.fetchall()

            for link in link_rows:
                actor_id = link["actorId"]
                cursor.execute("SELECT * FROM actors WHERE id = ?", (actor_id,))
                actor = cursor.fetchone()
                if actor:
                    movie_info["actors"].append({
                        "id": actor["id"],
                        "firstName": actor["firstName"],
                        "lastName": actor["lastName"]
                    })

            movies.append(movie_info)

    except Error as e:
        print(f"Error accessing the database: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return {"movies": movies}

@app.route("/movies/<int:movie_id>/review/new", methods=["POST"])
def add_review(movie_id):
    new_review = {}
    conn = None
    try:
        json_data = request.get_json()
        stars = json_data["stars"]
        description = json_data["description"]

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (moviesId, stars, description) VALUES (?, ?, ?)",
            (movie_id, stars, description)
        )
        conn.commit()

        new_review = {
            "id": cursor.lastrowid,
            "moviesId": movie_id,
            "stars": stars,
            "description": description
        }

    except Error as e:
        print(f"Error adding review: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return new_review

@app.route("/movies/title/<partial_title>")
def search_by_title(partial_title):
    movies = []
    conn = None
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM movies WHERE title LIKE ?", (f"%{partial_title}%",))
        rows = cursor.fetchall()

        for row in rows:
            movies.append({
                "id": row["id"],
                "title": row["title"],
                "year": row["year"]
            })

    except Error as e:
        print(f"Error searching by title: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return {"movies": movies}

@app.route("/movies/ratings/<int:min_rating>")
def search_by_min_rating(min_rating):
    movies = []
    conn = None
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM movies")
        movie_rows = cursor.fetchall()

        for movie in movie_rows:
            movie_id = movie["id"]
            cursor.execute("SELECT AVG(stars) AS avg_rating FROM reviews WHERE moviesId = ?", (movie_id,))
            avg_result = cursor.fetchone()

            if avg_result["avg_rating"] is not None and avg_result["avg_rating"] >= min_rating:
                movies.append({
                    "id": movie["id"],
                    "title": movie["title"],
                    "year": movie["year"],
                    "average_rating": avg_result["avg_rating"]
                })

    except Error as e:
        print(f"Error filtering by rating: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return {"movies": movies}

@app.route("/movies/actors/<name>")
def search_by_actor_name(name):
    results = []
    conn = None
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM actors WHERE firstName LIKE ? OR lastName LIKE ?",
            (f"%{name}%", f"%{name}%")
        )
        actor_rows = cursor.fetchall()

        for actor in actor_rows:
            actor_id = actor["id"]
            first_name = actor["firstName"]
            last_name = actor["lastName"]

            cursor.execute("SELECT * FROM actorsInMovies WHERE actorId = ?", (actor_id,))
            link_rows = cursor.fetchall()

            for link in link_rows:
                movie_id = link["movieId"]
                cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
                movie = cursor.fetchone()
                if movie:
                    results.append({
                        "movie": {
                            "id": movie["id"],
                            "title": movie["title"],
                            "year": movie["year"]
                        },
                        "actor": {
                            "id": actor_id,
                            "firstName": first_name,
                            "lastName": last_name
                        }
                    })

    except Error as e:
        print(f"Error searching by actor name: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return {"results": results}

@app.route("/movies/new", methods=["POST"])
def add_movie():
    new_movie = {}
    conn = None
    try:
        json_data = request.get_json()
        title = json_data["title"]
        year = json_data["year"]

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO movies (title, year) VALUES (?, ?)", (title, year))
        conn.commit()

        new_movie = {
            "id": cursor.lastrowid,
            "title": title,
            "year": year
        }

    except Error as e:
        print(f"Error adding movie: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return new_movie

@app.route("/actors/new", methods=["POST"])
def add_actor():
    new_actor = {}
    conn = None
    try:
        json_data = request.get_json()
        first_name = json_data["firstName"]
        last_name = json_data["lastName"]
        movie_id = json_data["movieId"]

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO actors (firstName, lastName) VALUES (?, ?)",
                       (first_name, last_name))
        actor_id = cursor.lastrowid

        cursor.execute("INSERT INTO actorsInMovies (actorId, movieId) VALUES (?, ?)", (actor_id, movie_id))
        conn.commit()

        new_actor = {
            "id": actor_id,
            "firstName": first_name,
            "lastName": last_name,
            "movieId": movie_id
        }

    except Error as e:
        print(f"Error adding actor: {e}")
        abort(500)
    finally:
        if conn:
            conn.close()

    return new_actor
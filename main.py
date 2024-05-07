from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os

auth_token = os.environ.get('AUTH_TOKEN')

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie.db"
db = SQLAlchemy()
db.init_app(app)


class RateMovieForm(FlaskForm):
    rating = FloatField("Your Rating out of 10 eg 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("SUBMIT")


class AddMovie(FlaskForm):
    movie_name = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("SUBMIT")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movie = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars()
    length = 1
    for movie in all_movie:
        movie.ranking = length
        length += 1
    db.session.commit()
    all_movie = db.session.execute(db.select(Movie).order_by(Movie.ranking.desc())).scalars()
    return render_template("index.html", all_movies=all_movie)


# @app.route("/")
# def home():
#     result = db.session.execute(db.select(Movie).order_by(Movie.rating))
#     all_movies = result.scalars().all() # convert ScalarResult to Python List
#
#     for i in range(len(all_movies)):
#         all_movies[i].ranking = len(all_movies) - i
#     db.session.commit()
#
#     return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    edit_form = RateMovieForm()
    movie_id = request.args.get("edit_id")
    movie_to_edit = db.get_or_404(Movie, movie_id)
    if edit_form.validate_on_submit():
        movie_to_edit.rating = edit_form.rating.data
        movie_to_edit.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", edit_movie=movie_to_edit, form=edit_form)


@app.route('/delete')
def delete():
    get_id = request.args.get('id')
    movie = db.get_or_404(Movie, get_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", 'POST'])
def add_movie():
    add_form = AddMovie()
    if add_form.validate_on_submit():
        movie_name = add_form.movie_name.data
        print(movie_name)
        url = f"https://api.themoviedb.org/3/search/movie?query={movie_name}"
        headers = {
            'Authorization': f"Bearer {auth_token}"
        }
        response = requests.get(url, headers=headers)
        data = response.json()["results"]
        print(data)
        return render_template("select.html", data=data)
    return render_template("add.html", form=add_form)


@app.route("/movie-details")
def movie_details():
    movie_id = request.args.get("movie_id")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    headers = {
        'Authorization': f"Bearer {auth_token}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)
    print(f"{data['title']}, description={data['overview']}")
    new_movie = Movie(title=data["title"],
                      year=data["release_date"].split("-")[0],
                      description=data["overview"],
                      img_url=f'https://image.tmdb.org/t/p/w500{data["poster_path"]}',
                      rating=0.0,
                      ranking=0,
                      review='give your own rating and review')
    db.session.add(new_movie)
    db.session.commit()
    db_id = db.session.execute(db.select(Movie).where(Movie.title == data["title"])).scalar()
    print(url_for('edit', edit_id=db_id.id))
    return redirect(url_for('edit', edit_id=db_id.id))


if __name__ == '__main__':
    app.run()

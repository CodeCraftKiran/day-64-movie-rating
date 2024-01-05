from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
API_KEY = "462bfd4421932b508f5c73a771701540"
auth_token= "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NjJiZmQ0NDIxOTMyYjUwOGY1YzczYTc3MTcwMTU0MCIsInN1YiI6IjY1OTUzNzU1ZDdhNzBhMTIyZTY5M2IzNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.CCmlLX7JqsKCbwhfJpzCiWnzgWnV01lW1vfCNpC7YjE"

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

new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, "
                "pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, "
                "Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)
second_movie = Movie(
    title="Avatar The Way of Water",
    year=2022,
    description="Set more than a decade after the events of the first film, "
                "learn the story of the Sully family (Jake, Neytiri, and their kids), "
                "the trouble that follows them, the lengths they go to keep each other safe, "
                "the battles they fight to stay alive, and the tragedies they endure.",
    rating=7.3,
    ranking=9,
    review="I liked the water.",
    img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
)
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.add(second_movie)
#     db.session.commit()



@app.route("/")
def home():
    all_movie = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars()

    return render_template("index.html", all_movies=all_movie)


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
    id = request.args.get('id')
    movie = db.get_or_404(Movie, id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET",'POST'])
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
    db_id = db.session.execute(db.select(Movie).where(Movie.title==data["title"])).scalar()
    print(url_for('edit', edit_id=db_id.id))
    return redirect(url_for('edit', edit_id=db_id.id))

if __name__ == '__main__':
    app.run(debug=True)

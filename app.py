from flask import Flask, render_template, url_for, redirect, request, flash
from flask_bootstrap import Bootstrap5
from flask_hashing import Hashing
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:7887@localhost/makdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

bootstrap = Bootstrap5(app)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

hashing = Hashing(app)

class Profile(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    firstname: Mapped[str]
    lastname: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
 
    posts = relationship("Post", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return self.username

    def hash_pass(password):
        return hashing.hash_value(password, salt="abcd")

class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profile.id"), primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)

    profile = relationship("Profile", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Comment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"))
    content: Mapped[str] = mapped_column(Text)

    post = relationship("Post", back_populates="comments", cascade="all")

    def __repr__(self):
        return f"Comment {self.id} on Post {self.post_id}"

@app.route("/")
def home():
    profiles = Profile.query.all()
    return render_template("base/home.html", profiles=profiles)

@app.route("/read/<int:id>", methods=["GET", "POST"])
def read(id):
    profile = Profile.query.get_or_404(id)
    if request.method == "POST":
        if "post_content" in request.form:
            title = f"Posted by: {profile.username}"
            content = request.form["post_content"]
            new_post = Post(profile_id=profile.id, title=title, content=content)
            db.session.add(new_post)
            db.session.commit()
            flash("Posted!")
        elif "comment_content" in request.form:
            post_id = request.form["post_id"]
            content = request.form["comment_content"]
            new_comment = Comment(post_id=post_id, content=content)
            db.session.add(new_comment)
            db.session.commit()
            flash("Commented!")
        
    posts = Post.query.filter_by(profile_id=id).all()
    return render_template("user/read.html", profile=profile, posts=posts)

@app.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        username = request.form["username"]
        password = request.form["password"]
        profile = Profile(firstname=firstname, lastname=lastname, username=username, password=Profile.hash_pass(password))
        db.session.add(profile)
        db.session.commit()
        flash(f"{username} added successfully")
    return render_template("user/create.html")

@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    profile = Profile.query.get_or_404(id)

    if request.method == "POST":
        profile.firstname = request.form["firstname"]
        profile.lastname = request.form["lastname"]
        db.session.commit()
        flash(f"{profile.username} updated successfully")
        return redirect(url_for("home"))

    return render_template("user/update.html", profile=profile)

@app.route("/delete/<int:id>")
def remove(id):
    profile = Profile.query.get_or_404(id)
    posts = Post.query.filter_by(profile_id=id).all()
    for post in posts:
        Comment.query.filter_by(post_id=post.id).delete()
        
    Post.query.filter_by(profile_id=id).delete()
    db.session.delete(profile)
    db.session.commit()
    flash("Deleted successfully")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)

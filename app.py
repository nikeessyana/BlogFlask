from flask import Flask, render_template, request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import *
import json
import math
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from sqlalchemy.testing.pickleable import User

app = Flask(__name__)

with open("config.json", "r") as c:
    param = json.load(c)["parameters"]

# Database
database_url = os.getenv("DATABASE_URL")

if database_url:
    # Production: Railway
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = param['local_uri']

# Secret key
app.config['SECRET_KEY'] = os.getenv(
    "SECRET_KEY",
    param['secret_key']
)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

class Contact(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    message = db.Column(db.String(500))
    date = db.Column(db.String(20))

class Post(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    content_1 = db.Column(db.Text)
    content_2 = db.Column(db.Text)
    date_post = db.Column(db.Date)
    author = db.Column(db.String(50))
    image = db.Column(db.String(300))
    location = db.Column(db.String(200))
    slug = db.Column(db.String(180),unique=True)

class Users(UserMixin, db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))
    # is_active = db.Column(db.Boolean)

@app.route('/')
def main():
    db.session.commit()
    post_data = Post.query.all()
    n = 5
    last = math.ceil(len(post_data)/n)
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page=1
    page = int(page)
    j = (page-1)*n
    posts = post_data[j:j+n]
    if j == 1 :
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page == last :
        next ="#"
        prev = "/?page="+ str(page-1)
    else :
        next = "/?page=" + str(page+1)
        prev = "/?page=" + str(page-1)
    return render_template("index.html", param=param, posts=post_data, prev=prev,next=next)

@app.route('/post/<slug>', methods=['GET'])
def post(slug):
    single_post = Post.query.filter_by(slug=slug).first()
    return render_template("post.html", param=param, post = single_post)

@app.route('/about')
def about():
    return render_template("about.html", param=param)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin'))
        else :
            flash("Invalid username or password")
            return redirect(url_for('login'))
    return render_template("login.html", param=param)

@app.route("/signup",methods=['GET','POST'])
def signup():
    if (request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.')
            return redirect(url_for('signup'))
        new_user = Users(name=name,email=email, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
    return render_template("signup.html",param=param)



@app.route('/contact', methods=['GET','POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        entry = Contact(name=name, email=email, message=message, date=datetime.today().date())
        db.session.add(entry)
        db.session.commit()
    return render_template("contact.html", param=param)

@app.route('/admin',methods=['GET', 'POST'])
@login_required
def admin():
    user = current_user.name
    style = ''
    posts = Post.query.filter_by(author=user).all()
    contacts = Contact.query.filter_by().all()
    if not current_user.username == "user123":
        style="display:none;"
    return  render_template("admin/index.html",posts=posts,contacts=contacts, style=style)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/editPost/<string:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if request.method=='POST':
        ntitle = request.form.get('title')
        nsubtitle = request.form.get('subtitle')
        nauthor = current_user.name
        nimage = request.form.get('image')
        nlocation = request.form.get('location')
        nslug = request.form.get('slug')
        ndate = request.form.get('date')
        ncontent1 = request.form.get('content1')
        ncontent2 = request.form.get('content2')
        if post_id=='0':  #add a new post in db
            post = Post(title=ntitle, subtitle=nsubtitle,location=nlocation,
                         content_1=ncontent1,content_2=ncontent2,author=nauthor, image=nimage,slug=nslug,
                         date_post=ndate)
            db.session.add(post)
            db.session.commit()
        else:
            post = Post.query.filter_by(post_id=post_id).first()
            post.title=ntitle
            post.subtitle=nsubtitle
            post.author = nauthor
            post.image = nimage
            post.location = nlocation
            post.date_post = ndate
            post.content_1 = ncontent1
            post.content_2 = ncontent2
            post.slug=nslug
            db.session.commit()
        return redirect(url_for('admin'))
    post = Post.query.filter_by(post_id=post_id).first()
    return render_template('admin/editPost.html',param=param,post=post,post_id=post_id)


@app.route('/delete/<string:post_id>', methods=['GET', 'POST'])
def delete(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/deleteContact/<string:contact_id>', methods=['GET', 'POST'])
def deleteContact(contact_id):
    cont = Contact.query.filter_by(contact_id=contact_id).first()
    db.session.delete(cont)
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)

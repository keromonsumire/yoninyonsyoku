from operator import truediv
from flask import Flask
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

 

from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import pytz
import os
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

login_manager = LoginManager() 
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
    blogarticles = db.relationship('BlogArticle', backref='users', lazy=True)


class BlogArticle(db.Model):
    __tablename__ = 'BlogArticle'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    tag_relation = db.relationship('Tag_relation', backref='BlogArticle', lazy=True)
    
class Tag_relation(db.Model):
    __tablename__ = 'Tagrelation' 
    relation_id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('Tag.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('BlogArticle.id'))

class Tag(db.Model):
    __tablename__ = 'Tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tag_relation = db.relationship('Tag_relation', backref='Tag', lazy=True)



 


@app.route('/', methods=['GET'])
def blog():
    #ユーザーがログインしていれば
    if current_user.is_authenticated:
        if request.method == 'GET':
            # DBに登録されたデータをすべて取得する
            blogarticles = BlogArticle.query.all()
            
            # 辞書を作成　　　辞書内に配列を作成
            tags = {}
            # 投稿idを取得
            for blogarticle in blogarticles:
                #blogarticleのidと一致するものをTag_relationから取得
                relation_to_tags = Tag_relation.query.filter_by(article_id=blogarticle.id)
                #配列を作成
                box = []
                for relation_to_tag in relation_to_tags:
                    #Tagからnameを取得
                    tag = Tag.query.filter_by(id = relation_to_tag.tag_id).first()
                    box.append(tag.name)
                tags[blogarticle.id] = box
            
        print(tags)
        return render_template('index.html', blogarticles=blogarticles, tags = tags)
    else:
        return redirect('/login')

#ユーザー登録
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        # Userのインスタンスを作成
        user = User(username=username, password=generate_password_hash(password, method='sha256'))
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

#ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Userテーブルからusernameに一致するユーザを取得
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/create', methods=['GET', 'POST'])
@login_required

def create():
    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('body')
        tag = request.form.get('tag')
        
        # BlogArticleのインスタンスを作成
        blogarticle = BlogArticle(title=title, body=body, user_id=current_user.id)
        db.session.add(blogarticle)
        db.session.commit()

        # Tagのインスタンスを作成
        Tag_instance = Tag(name = tag)
        db.session.add(Tag_instance)
        db.session.commit()

        #  Tag_relationにarticle_idを記録
        # 最新のBlogArticleから、idを取得し、そのidをrticle_idとしてTag_relationに保存
        # 最新のTagテーブルからidを取得し、そのidをTag_relationに保存
        relation_article = BlogArticle.query.order_by(BlogArticle.id.desc()).first()
        relation_tag= Tag.query.order_by(Tag.id.desc()).first()
        
        tagrelation= Tag_relation(tag_id =relation_tag.id,article_id=relation_article.id)
        db.session.add(tagrelation)
        db.session.commit()
       
        return redirect('/')
    else:
        return render_template('create.html')
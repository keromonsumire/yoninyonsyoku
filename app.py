import numbers
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contents = db.relationship('Content', backref='BlogArticle')
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

class Content(db.Model):
    __tablename__ = 'contents'
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('BlogArticle.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text)
    seq = db.Column(db.Integer, nullable=False)


@app.route('/', methods=['GET'])
def blog():
    #ユーザーがログインしていれば
    if current_user.is_authenticated:
        if request.method == 'GET':
            # DBに登録されたデータをすべて取得する
            blogarticles = BlogArticle.query.all()
            
            # 辞書を作成　　　辞書内に配列を作成
            tags = {}
            names = {}
            # 投稿idを取得
            for blogarticle in blogarticles:
                #blogの投稿主を取得
                user = User.query.filter_by(id=blogarticle.user_id).all()
                #ユーザーネームをnames辞書に記録
                names[blogarticle.id] = user[0].username
                #blogarticleのidと一致するものをTag_relationから取得
                relation_to_tags = Tag_relation.query.filter_by(article_id=blogarticle.id)
                #配列を作成
                box = []
                for relation_to_tag in relation_to_tags:
                    #Tagからnameを取得
                    tag = Tag.query.filter_by(id = relation_to_tag.tag_id).first()
                    box.append(tag.name)
                tags[blogarticle.id] = box
        
        return render_template('index.html', blogarticles=blogarticles, tags = tags, names = names)

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
        #tag = request.form.get('tag')
        tag = []
        headline = []
        body = []
        for num in range(5): 
            body.append(request.form.get(f'body{num+1}'))
            headline.append(request.form.get(f'headline{num+1}'))
            tag.append(request.form.get(f'tag{num+1}'))
        
        # BlogArticleのインスタンスを作成
        blogarticle = BlogArticle(title=title, user_id=current_user.id, )
        db.session.add(blogarticle)
        db.session.commit()

        #最新の記事(今作成した記事)を取得
        blog = BlogArticle.query.order_by(BlogArticle.id.desc()).limit(1).all() 
        blog_id = blog[0].id 
        count = 0
        #formの数だけ繰り返す
        for num in range(5):
            #formが入力されていなければデータベースに入れない
            if headline[num] != "":
                new_headline = Content(blog_id=blog_id, content_type="headline", text=headline[num],seq=count)
                db.session.add(new_headline)
                count += 1
            if body[num] != "":
                new_body = Content(blog_id=blog_id, content_type="body", text=body[num], seq=count)
                db.session.add(new_body)
                count += 1
        db.session.commit()
        # Tagのインスタンスを作成, Tagのテーブルに追加
        count_newtag = 0
        #formの数だけ繰り返す
        for num in range(5):
            #formが入力されていなければデータベースに入れない
            if tag[num] != "":
                tag_existance = Tag.query.filter_by(name = tag[num]).first()
                # tag_existanceがNoneであれば、新しくTagテーブルに追加
                if tag_existance is None:
                    new_tag = Tag(name = tag[num]).first()
                    db.session.add(new_tag)
                    count_newtag += 1
        db.session.commit()

        for num in range(len(tag)):
            #Tagテーブルの中に存在するか調べる
            tag_existance = Tag.query.filter_by(name = tag[num]).first()
            #もし存在すれば、Tag_relationに追加
            if  tag_existance is not None:
                tagrelation = Tag_relation(tag_id =tag_existance.id, article_id=blog_id).first()
                print(tagrelation)
                db.session.add(tagrelation)
        db.session.commit()
       
        return redirect('/')
    else:
        return render_template('create.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    # 引数idに一致するデータを取得する
    blogarticle = BlogArticle.query.get(id)
    if request.method == "GET":
        return render_template('update.html', blogarticle=blogarticle)
    else:
        # 上でインスタンス化したblogarticleのプロパティを更新する
        blogarticle.title = request.form.get('title')
        blogarticle.body = request.form.get('body')
        # 更新する場合は、add()は不要でcommit()だけでよい
        db.session.commit()
        return redirect('/user/show')


@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    # 引数idに一致するデータを取得する
    blogarticle = BlogArticle.query.get(id)
    db.session.delete(blogarticle)
    db.session.commit()
    return redirect('/user/show')





@app.route('/user/show')
def show_user():
    user_id = current_user.id
    blogarticles = BlogArticle.query.filter_by(user_id=user_id).all()
    content = {}
    for blogarticle in blogarticles:
        contents = Content.query.filter_by(blog_id=blogarticle.id).order_by(Content.seq).all()
        box = []
        for c in contents:
            dic = {}
            dic["type"] = c.content_type
            dic["text"] = c.text
            box.append(dic)
        content[blogarticle.id] = box
        
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

    return render_template('show_user.html', blogarticles=blogarticles, content=content, tags = tags)

@app.route('/article/<int:id>')
def show_article(id):
    blogarticle = BlogArticle.query.get(id)
    user = User.query.filter_by(id=blogarticle.user_id).all()
    user_name = user[0].username
    contents = Content.query.filter_by(blog_id=blogarticle.id).order_by(Content.seq).all()
    return render_template('show_article.html', blogarticle=blogarticle, contents=contents, user_name=user_name)

import numbers
from operator import truediv
from flask import Flask
from flask import render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy


from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import pytz
import os, sys
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image

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
    image = db.Column(db.String(100))

    
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
    type_id = db.Column(db.Integer)

class Content(db.Model):
    __tablename__ = 'contents'
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('BlogArticle.id'))
    content_type = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text)
    seq = db.Column(db.Integer, nullable=False)

@app.route('/welcome', methods=['GET'])
def welcome():
    return render_template('welcome.html')

@app.route('/information/search', methods=['GET'])
def info_search():
    return render_template('information_search.html')

@app.route('/information/write',methods=['GET'])
def info_write():
    return render_template('information_write.html')

@app.route('/', methods=['GET', 'POST'])
def blog():
    #ユーザーがログインしていれば
    if current_user.is_authenticated:
        if request.method == 'GET':
            # DBに登録されたデータをすべて取得する
            blogarticles = BlogArticle.query.all()
            # 辞書を作成　　　辞書内に配列を作成
            tags = {}
            return render_template('index.html', blogarticles=[], tags = [], names = [])
                    #タイプで検索をする # checkboxからtypeを取得
        elif request.method == "POST":
            types = request.form.getlist("check")
            ##もしなにも選択していない場合  ##までつづく
            if types == []:
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
                        tag_dict = {}
                        tag = Tag.query.filter_by(id = relation_to_tag.tag_id).first()
                        tag_dict["name"] = tag.name
                        tag_dict["type"] = tag.type_id
                        box.append(tag_dict)
                    tags[blogarticle.id] = box
                flash('チェック入れて検索してください')
                return render_template('index.html', blogarticles=blogarticles, tags = tags, names = names)
                ##
            #checkboxでチェックを入れたタイプからTagのインスタンスを生成
            tags = Tag.query.filter(Tag.type_id.in_(types)).all()
            #tagsのid==Tagrelationsのtag_idであるTag_relationのインスタンスを作成し、article_idの配列をつくる
            #配列を作成
            relation_box = []
            for tag in tags:
                tagrelation = Tag_relation.query.filter_by(tag_id = tag.id).first()
                relation_box.append(tagrelation.article_id)
            
            blogarticles = BlogArticle.query.filter(BlogArticle.id.in_(relation_box)).all()
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
                    tag_dict = {}
                    tag = Tag.query.filter_by(id = relation_to_tag.tag_id).first()
                    tag_dict["name"] = tag.name
                    tag_dict["type"] = tag.type_id
                    box.append(tag_dict)
                tags[blogarticle.id] =  box
            print(blogarticles) 
            if blogarticles == []:
                flash('この検索内容では記事がありません')

            return render_template('search.html', blogarticles=blogarticles, tags = tags, names = names)

    else:
        return redirect('/login')

 


#タイプによる登録
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        # Userのインスタンスを作成
        if User.query.filter_by(username=username).first() is None:
            if username == '' or password == '':
                flash('ユーザー名とパスワードを入力してください')
                return render_template('signup.html')
            else:
                user = User(username=username, password=generate_password_hash(password, method='sha256'))
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
        else:
            flash('そのユーザー名はすでに登録されています')
            return render_template('sesarch.html')
    else:
        return render_template('index.html')




#ユーザー登録
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        # Userのインスタンスを作成
        if User.query.filter_by(username=username).first() is None:
            if username == '' or password == '':
                flash('ユーザー名とパスワードを入力してください')
                return render_template('signup.html')
            else:
                user = User(username=username, password=generate_password_hash(password, method='sha256'))
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
        else:
            flash('そのユーザー名はすでに登録されています')
            return render_template('signup.html')
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
        if user == None:
            flash('そのユーザー名は存在しません')
            return render_template('login.html')
        elif check_password_hash(user.password, password):
            login_user(user)
            session["is_login"] = True
            return redirect('/')
        else:
            flash("メールアドレスもしくはパスワードが異なります")
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session["is_login"] = False
    return redirect('/login')

@app.route('/create', methods=['GET', 'POST'])
@login_required

def create():
    if request.method == "POST":
        title = request.form.get('title')
        headline = []
        body = []
        for num in range(5): 
            body.append(request.form.get(f'body{num+1}'))
            headline.append(request.form.get(f'headline{num+1}'))
        if title == "":
            flash('タイトルを入力してください')
            return render_template("create.html")
        elif len(title) > 50:
            flash('タイトルは50文字以下にしてください')
            return render_template("create.html")
        elif headline[0] == "":
            flash('見出しを入力してください')
            return render_template("create.html")
        elif body[0] == "":
            flash('内容を入力してください')
            return render_template("create.html")
        else:
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

            session["blog_id"] = blog[0].id
            return redirect('/create/tag')
    else:
        return render_template('create.html')

@app.route('/create/tag',methods=['GET', 'POST'])
def create_tag():
    blogarticle = BlogArticle.query.get(session["blog_id"])
    if request.method == "GET":
        tag1 = Tag.query.filter_by(type_id=1).all()
        tag2 = Tag.query.filter_by(type_id=2).all()
        tag3 = Tag.query.filter_by(type_id=3).all()
        tag4 = Tag.query.filter_by(type_id=4).all()
        tag5 = Tag.query.filter_by(type_id=5).all()
        return render_template('create_tag.html',tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4, tag5=tag5)
    else:
        tag = []
        for number in range(5): 
            for num in range(5):
                tag.append(request.form.get(f'tag{number+1}-{num+1}'))
        for num in range(25):
            #tagが入力されていなければデータベースに入れない
            if tag[num] != "":
                tag_existance = Tag.query.filter_by(name = tag[num]).first()
                # tag_existanceがNoneであれば、新しくTagテーブルに追加
                if tag_existance is None:
                    new_tag = Tag(name = tag[num])
                    db.session.add(new_tag)
        db.session.commit()
        for number in range(5):
            for num in range(5):
                #Tagテーブルの中に存在するか調べる
                tag_existance = Tag.query.filter_by(name = tag[number * 5 + num]).first()
                #もし存在すれば、Tag_relationに追加
                if  tag_existance is not None:
                    tagrelation = Tag_relation(tag_id =tag_existance.id, article_id=session["blog_id"])
                    print(tagrelation)
                    tag_existance.type_id = number + 1
                    db.session.add(tagrelation)
        existing_tag_ids = request.form.getlist("existing")
        print(existing_tag_ids)
        for tag_id in existing_tag_ids:
            tagrelation = Tag_relation(tag_id=tag_id, article_id=session["blog_id"])
            db.session.add(tagrelation)
        db.session.commit()
        return redirect('/upload')


@app.route('/update/<int:id>',methods=['GET', 'POST'])
def update(id):
    # 引数idに一致するデータを取得する➡blogarticleのデータを取得
    blogarticle = BlogArticle.query.get(id)
    content = Content.query.filter_by(blog_id=id).all()
    headlines = Content.query.filter_by(content_type="headline").filter_by(blog_id=id).all()
    bodys = Content.query.filter_by(content_type="body").filter_by(blog_id=id).all()
    length = len(headlines)
    


    if request.method == "GET":
        return render_template('update.html', blogarticle=blogarticle, content=content,headlines=headlines,bodys=bodys,length=length)
    else:
        # 上でインスタンス化したblogarticleのプロパティを更新する
        blogarticle.title = request.form.get('title')
        for number in range(length):
            headlines[number].text = request.form.get(f'headline{number}')
            bodys[number].text = request.form.get(f'body{number}')

        
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
    tag_relations = Tag_relation.query.filter_by(article_id = id).all()
    tags = []
    for relation in tag_relations:
        tag = Tag.query.filter_by(id=relation.tag_id).first()
        tags.append(tag)
    return render_template('show_article.html', blogarticle=blogarticle, contents=contents, user_name=user_name, tags=tags)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    elif request.method == 'POST':
        file = request.files['image']
        file.save(os.path.join('./static/image', file.filename))
        im = Image.open(f"./static/image/{file.filename}")
        out = im.resize((128, 128))
        out.save(f"./static/image/{file.filename}")
                    
        blogarticle = BlogArticle.query.filter_by(id = session["blog_id"]).all()
        blogarticle[0].image = file.filename

        db.session.commit()
        return redirect('/')

@app.route('/uploaded_file/<string:filename>')
def uploaded_file(filename):
    return render_template('uploaded_file.html', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)


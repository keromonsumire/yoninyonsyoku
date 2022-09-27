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
import MeCab
from flask_fontawesome import FontAwesome

app = Flask(__name__)
db_uri = os.environ.get('DATABASE_URL') or "sqlite:///blog.db"
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
fa = FontAwesome(app)

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
    comments = db.relationship('Comment', backref='users', lazy=True)

class BlogArticle(db.Model):
    __tablename__ = 'BlogArticle'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contents = db.relationship('Content', backref='BlogArticle')
    tag_relation = db.relationship('Tag_relation', backref='BlogArticle', lazy=True)
    image = db.Column(db.String(100))
    comments = db.relationship('Comment', backref='BlogArticle', lazy=True)

    
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

class Comment(db.Model):
    __tablename__ = 'Comment'
    comment_id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('BlogArticle.id'))
    contributor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))

class Like(db.Model):
    __tablename__ = 'Like'
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('BlogArticle.id'))
    user = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))


@app.route('/', methods=['GET'])
def welcome():
    return render_template('welcome.html')

@app.route('/information/search', methods=['GET'])
def info_search():
    return render_template('information_search.html')

@app.route('/login_session/<int:id>', methods=['GET','POST'])
def login_session(id):
    session["redirect_id"] = id

    return redirect('/login')

@app.route('/information/write',methods=['GET'])
def info_write():
    return render_template('information_write.html')

@app.route('/select', methods=['GET', 'POST'])
def blog():
#ユーザーがログインしていれば
    if request.method == 'GET':
        return render_template('index.html', blogarticles=[], tags = [], names = [])

    #タイプで検索をする # checkboxからtypeを取得
    elif request.method == "POST":
        
        #AND検索を押したら　r = "AND検索"
        r = request.form.get("andsearch")
        types = request.form.getlist("check")
        
        ##もしなにも選択していない場合  ##までつづく
        if types == []:
            flash('チェック入れて検索してください', 'ng')
            return redirect('select')

        #OR検索かAND検索かの識別
        if r =="AND検索":
            #５つのタイプがあるからそれぞれで繰り返す
            box =[]
            for i in [1,2,3,4,5]:
                #typesのなかにそれぞれの数字があれば、チェックボックスにチェックしたということでif文内へ
                if f"{i}" in types:
                    
                    #タイプを満たすtagのidを取得
                    tags_to_relations = Tag.query.filter(Tag.type_id== i).all()
                    Box =[]
                    #tagのidを満たすTag_relationを取得
                    #配列の中へ
                    for tags_to_relation in tags_to_relations:
                        relations = Tag_relation.query.filter_by(tag_id = tags_to_relation.id).all()
                        for relation in relations:
                            Box.append(relation.article_id)
                    box.append(Box)

            get_list = []
            #ここでboxは二次元配列
            #box内の配列で共通のidだけ取得
            for i in range(len(box)):
                if i == 0 :
                    merge = f"set(box[{i}])"
                else:
                    merge += f" & set(box[{i}])"
            #文字列を実行
            get_list = eval(merge)
            #共通のidからTag_relationのインスタンスを生成
            relation_merges = Tag_relation.query.filter(Tag_relation.article_id.in_(get_list)).all()
            
            relation_box = []
            for relation_merge in relation_merges:
                
                relation_box.append(relation_merge.article_id)

            blogarticles = BlogArticle.query.filter(BlogArticle.id.in_(relation_box)).order_by(BlogArticle.id.desc()).all()
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
            if blogarticles == []:
                flash('この検索内容では記事がありません', 'ng')

            return render_template('search.html', blogarticles=blogarticles, tags = tags, names = names, types = types)
        #or検索
        else:
            tags = Tag.query.filter(Tag.type_id.in_(types)).all()
            #tagsのid==Tagrelationsのtag_idであるTag_relationのインスタンスを作成し、article_idの配列をつくる
            #配列を作成
            relation_box = []
            for tag in tags:
                tagrelations = Tag_relation.query.filter_by(tag_id = tag.id).all()
                for tagrelation in tagrelations:
                    relation_box.append(tagrelation.article_id)
            
            blogarticles = BlogArticle.query.filter(BlogArticle.id.in_(relation_box)).order_by(BlogArticle.id.desc()).all()
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
            if blogarticles == []:
                flash('この検索内容では記事がありません', 'ng')

            return render_template('search.html', blogarticles=blogarticles, tags = tags, names = names, types = types)

 
#search
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == "POST":
        
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
                flash('ユーザー名とパスワードを入力してください', 'ng')
                return render_template('signup.html')
            else:
                user = User(username=username, password=generate_password_hash(password, method='sha256'))
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
        else:
            flash('そのユーザー名はすでに登録されています', 'ng')
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
            flash('そのユーザー名は存在しません', 'ng')
            return render_template('login.html')
        elif check_password_hash(user.password, password):
            login_user(user)
            session["is_login"] = True

            if "redirect_id" in session:
                return redirect (f'article/{session["redirect_id"]}')
            else:
                return redirect('/create')
        else:
            flash("メールアドレスもしくはパスワードが異なります", 'ng')


        return render_template('login.html')
    else:
        return render_template('login.html')

#ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session["is_login"] = False
    return redirect('/login')

#記事作成
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
            flash('タイトルを入力してください', 'ng')
            return render_template("create.html")
        elif len(title) > 50:
            flash('タイトルは50文字以下にしてください', 'ng')
            return render_template("create.html")
        elif headline[0] == "":
            flash('見出しを入力してください')
            return render_template("create.html", 'ng')
        elif body[0] == "":
            flash('内容を入力してください', 'ng')
            return render_template("create.html", 'ng')
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

#タグ作成
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
        m = MeCab.Tagger()
        tag = []
        count = 0
        for number in range(5): 
            for num in range(5):
                if request.form.get(f'tag{number+1}-{num+1}') != "":
                    count += 1
                    results = m.parse(request.form.get(f'tag{number+1}-{num+1}')).split()
                    if not results[-2].startswith('動詞'):
                        flash('タグは動詞系で入力してください', 'ng')
                        tag1 = Tag.query.filter_by(type_id=1).all()
                        tag2 = Tag.query.filter_by(type_id=2).all()
                        tag3 = Tag.query.filter_by(type_id=3).all()
                        tag4 = Tag.query.filter_by(type_id=4).all()
                        tag5 = Tag.query.filter_by(type_id=5).all()
                        return render_template('create_tag.html',tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4, tag5=tag5)  
                tag.append(request.form.get(f'tag{number+1}-{num+1}'))    
        existing_tag_ids = request.form.getlist("existing")
        count += len(existing_tag_ids)
        if count > 5 or count < 3:
            flash('必ず3〜5個の魅力タグを追加してください', 'ng')
            tag1 = Tag.query.filter_by(type_id=1).all()
            tag2 = Tag.query.filter_by(type_id=2).all()
            tag3 = Tag.query.filter_by(type_id=3).all()
            tag4 = Tag.query.filter_by(type_id=4).all()
            tag5 = Tag.query.filter_by(type_id=5).all()
            return render_template('create_tag.html',tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4, tag5=tag5)
        
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
                    tag_existance.type_id = number + 1
                    db.session.add(tagrelation)
        


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

#タグ追加
@app.route('/add_tag/<int:id>', methods=['GET','POST'])
def add_tag(id):
    blogarticle = BlogArticle.query.get(id)
    if request.method == "GET":
        relations = Tag_relation.query.filter_by(article_id=id).all()
        tag_ids =[]
        for relation in relations:
            tag_ids.append(relation.tag_id)
        
        tag1 = Tag.query.filter_by(type_id=1).filter(~Tag.id.in_(tag_ids)).all()
        tag2 = Tag.query.filter_by(type_id=2).filter(~Tag.id.in_(tag_ids)).all()
        tag3 = Tag.query.filter_by(type_id=3).filter(~Tag.id.in_(tag_ids)).all()
        tag4 = Tag.query.filter_by(type_id=4).filter(~Tag.id.in_(tag_ids)).all()
        tag5 = Tag.query.filter_by(type_id=5).filter(~Tag.id.in_(tag_ids)).all()
        return render_template('create_tag.html',tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4, tag5=tag5)
    else:
        m = MeCab.Tagger()
        tag = []
        count = 0
        for number in range(5): 
            for num in range(5):
                if request.form.get(f'tag{number+1}-{num+1}') != "":
                    count += 1
                    results = m.parse(request.form.get(f'tag{number+1}-{num+1}')).split()
                    if not results[-2].startswith('動詞'):
                        flash('タグは動詞で入力してください', 'ng')
                        tag1 = Tag.query.filter_by(type_id=1).all()
                        tag2 = Tag.query.filter_by(type_id=2).all()
                        tag3 = Tag.query.filter_by(type_id=3).all()
                        tag4 = Tag.query.filter_by(type_id=4).all()
                        tag5 = Tag.query.filter_by(type_id=5).all()
                        return render_template('create_tag.html',tag1=tag1, tag2=tag2, tag3=tag3, tag4=tag4, tag5=tag5)  
                tag.append(request.form.get(f'tag{number+1}-{num+1}'))
        count += len(Tag_relation.query.filter_by(article_id=id).all())
        existing_tag_ids = request.form.getlist("existing")
        count += len(existing_tag_ids)
        if count > 5:
            flash('魅力はタグは５個までしか持てません', 'ng')
            return redirect(f'/add_tag/{id}')   

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
                    tagrelation = Tag_relation(tag_id =tag_existance.id, article_id=id)
                    print(tagrelation)
                    tag_existance.type_id = number + 1
                    db.session.add(tagrelation)

        for tag_id in existing_tag_ids:
            tagrelation = Tag_relation(tag_id=tag_id, article_id=id)
            db.session.add(tagrelation)
        db.session.commit()
        return redirect('/user/show')

#タグ削除
@app.route('/delete_tag/<int:id>', methods=['GET','POST'])
def delete_tag(id):
    blogarticle = BlogArticle.query.get(id)
    if request.method == "GET":
        tag_ids=[]
        tag_relations = Tag_relation.query.filter_by(article_id=id).all()
        for tag_relation in tag_relations:
            tag_ids.append(tag_relation.tag_id)
        tag_names=[]
        for tag_id in tag_ids:
            tag = Tag.query.filter_by(id=tag_id).first()
            tag_names.append(tag.name)
        return render_template('delete_tag.html', tag_names = tag_names)
    else:
        tag_names = request.form.getlist("tag")
        count = len(Tag_relation.query.filter_by(article_id=id).all()) - len(tag_names)
        if count < 3:
            flash('タグは必ず３個以上つけてください', 'ng')
            return redirect(f'/delete_tag/{id}')
        tag_ids=[]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            tag_ids.append(tag.id)
        for tag_id in tag_ids:
            tag_relation = Tag_relation.query.filter_by(tag_id=tag_id).filter_by(article_id=id).first()
            db.session.delete(tag_relation)
            db.session.commit()
            if Tag_relation.query.filter_by(tag_id=tag_id).first() is None:
                tag = Tag.query.filter_by(id=tag_id).first()
                db.session.delete(tag)
                db.session.commit()
        return redirect('/user/show')

#投稿削除
@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    # 引数idに一致するデータを取得する
    blogarticle = BlogArticle.query.get(id)
    tagrelations = Tag_relation.query.filter_by(article_id=id).all()
    tag_ids = []
    #tagrelationの削除
    for tagrelation in tagrelations:
        tag_ids.append(tagrelation.tag_id)
        db.session.delete(tagrelation)
    db.session.delete(blogarticle)
    db.session.commit()
    #どの記事にも紐づいていないタグの削除
    for tag_id in tag_ids:
        tagrelation = Tag_relation.query.filter_by(tag_id=tag_id).first()
        if tagrelation is None:
            tag = Tag.query.filter_by(id=tag_id).first()
            db.session.delete(tag)
    db.session.commit()
    return redirect('/user/show')

#コメント削除
@app.route('/delete_comment/<int:commentid>', methods=['GET'])
def delete_comment(commentid):
    # 引数commentidに一致するデータを取得する
    comment = Comment.query.filter_by(comment_id = commentid).first()
    #戻る記事の番号を取得
    blogarticle  = BlogArticle.query.filter_by( id = comment.blog_id).first()
    page = blogarticle.id
    #コメント削除
    db.session.delete(comment)
    db.session.commit()
    return redirect(f'/article/{page}')


#自分の投稿一覧
@app.route('/user/show')
def show_user():
    user_id = current_user.id
    blogarticles = BlogArticle.query.filter_by(user_id=user_id).order_by(BlogArticle.created_at.desc()).all()
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
    likes = {}
    # 投稿idを取得
    for blogarticle in blogarticles:
        #blogarticleのidと一致するものをTag_relationから取得        
        relation_to_tags = Tag_relation.query.filter_by(article_id=blogarticle.id)
        likes[blogarticle.id] = len(Like.query.filter_by(blog_id=blogarticle.id).all())
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

    return render_template('show_user.html', blogarticles=blogarticles, content=content, tags = tags, likes=likes)

#個別記事の表示
@app.route('/article/<int:id>', methods=['GET', 'POST'])
def show_article(id):
    blogarticle = BlogArticle.query.get(id)
    like_count = len(Like.query.filter_by(blog_id=id).all())
    like_check = True
    if Like.query.filter_by(blog_id=id).filter_by(user=request.remote_addr).first() is None:
            like_check = False
    if request.method == "GET":
        user = User.query.filter_by(id=blogarticle.user_id).all()
        user_name = user[0].username
        contents = Content.query.filter_by(blog_id=blogarticle.id).order_by(Content.seq).all()
        tag_relations = Tag_relation.query.filter_by(article_id = id).all()
        tags = []
        for relation in tag_relations:
            tag = Tag.query.filter_by(id=relation.tag_id).first()
            tags.append(tag)
        comments = Comment.query.order_by(Comment.comment_id.desc()).filter_by(blog_id=blogarticle.id).all()
        comment_names = {}
        for comment in comments:
            user = User.query.filter_by(id=comment.contributor_id).all()
            comment_names[comment.contributor_id] = user[0].username

            

        return render_template('show_article.html', blogarticle=blogarticle, contents=contents, user_name=user_name, tags=tags, comments=comments, current_user=current_user, comment_names = comment_names, like_count=like_count, like_check = like_check)
    #コメントしたとき    

    else:
        comment = request.form.get('comment')
        comment_instance = Comment(blog_id = id, contributor_id = current_user.id, text = comment)
        db.session.add(comment_instance)
        db.session.commit()

        user = User.query.filter_by(id=blogarticle.user_id).all()
        user_name = user[0].username
        contents = Content.query.filter_by(blog_id=blogarticle.id).order_by(Content.seq).all()
        tag_relations = Tag_relation.query.filter_by(article_id = id).all()
        tags = []
        for relation in tag_relations:
            tag = Tag.query.filter_by(id=relation.tag_id).all()
            tags.append(tag)

        #コメントを表示するところ
        comments = Comment.query.order_by(Comment.comment_id.desc()).filter_by(blog_id=blogarticle.id).all()
        comment_names = {}
        for comment in comments:
            user = User.query.filter_by(id=comment.contributor_id).all()
            comment_names[comment.contributor_id] = user[0].username


        
        return render_template('show_article.html', blogarticle=blogarticle, contents=contents, user_name=user_name, tags=tags, comments=comments, current_user=current_user, comment_names = comment_names, like_count=like_count, like_check = like_check)



#画像のアップロード
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    elif request.method == 'POST':
        file = request.files['image']
        if file.filename.endswith("png") or file.filename.endswith("jpeg") or file.filename.endswith("jpg") or file.filename.endswith("gif"):
            file.save(os.path.join('./static/image', file.filename))
            im = Image.open(f"./static/image/{file.filename}")
            out = im.resize((312, 312))
            out.save(f"./static/image/{file.filename}")    
            blogarticle = BlogArticle.query.filter_by(id = session["blog_id"]).all()
            blogarticle[0].image = file.filename
            db.session.commit()
            flash('投稿ありがとうございます', 'pg')
            return redirect('/user/show')
        else:
            flash('jpeg, png, gifのどれかにしてください', 'ng')
            return redirect('/upload')

#画像をアップデートする際にその記事のIDをセッションに格納
@app.route('/image_update/<int:id>', methods=['GET'])
def image_update(id):
    if request.method == 'GET':
        session["blog_id"] = id
        return render_template('upload.html')


@app.route('/like/<int:id>', methods=['GET'])
def like(id):
    if request.method == 'GET':
        existance = Like.query.filter_by(blog_id=id).filter_by(user=request.remote_addr).first()
        print(existance)
        print(request.remote_addr)
        if existance is None:
            like = Like(blog_id=id, user=request.remote_addr)
            print(like)
            db.session.add(like)
        else:
            db.session.delete(existance)
        db.session.commit()
        return redirect(f'/article/{id}')

if __name__ == '__main__':
    app.run(debug=True)



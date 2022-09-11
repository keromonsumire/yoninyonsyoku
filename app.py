from flask import Flask
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from flask import render_template, request, redirect
 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)
 
 
class BlogArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
 
@app.route('/')
def blog():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('body')
        # BlogArticleのインスタンスを作成
        blogarticle = BlogArticle(title=title, body=body)
        db.session.add(blogarticle)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('create.html')
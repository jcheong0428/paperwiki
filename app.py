# App from sanic
from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms.fields import SubmitField
from flask_pagedown import PageDown
# for markdown
import markdown
from flask import Markup
from crossref.restful import Works

class PageDownFormExample(FlaskForm):
    pagedown = PageDownField('Enter your markdown')
    submit = SubmitField('Submit')

# Handle mongo queries async style
from motor.motor_asyncio import AsyncIOMotorClient
from flask_pymongo import PyMongo

# Template rendering
# from jinja2 import DictLoader
# import jinja2_sanic as j2s
# External async connections
import asyncio
import uvloop
# Utils
# from sanic.response import json
import os, subprocess, threading
import json
from datetime import datetime

# Scholar searcher.
from scholar import SearchScholarQuery, ScholarQuerier, SearchScholarQuery,ScholarSettings

# Create app
app = Flask(__name__)
pagedown = PageDown(app)
# app.db = AsyncIOMotorClient(app.config['MONGOURI'])['paperwiki']
on_heroku = os.getenv("ON_HEROKU", False)
if on_heroku:
    app.config["MONGO_URI"] = os.getenv("MONGOURI")
else:
    app.config.from_pyfile('./config.py')
    app.config["MONGO_URI"] = app.config['MONGOURI']

app.config.update(dict(
    SECRET_KEY="powerful secretkey yes!",
    WTF_CSRF_SECRET_KEY="a csrf secret key"
))

mongo = PyMongo(app)
# session = {}
# @app.middleware('request')
# def add_session(request):
#     request['session'] = session

# Configure templates
# template_dict = {}
# template_dict['home'] = open('./templates/home.html').read()
# template_dict['see_wiki'] = open('./templates/see_wiki.html').read()
# template_dict['create_wiki'] = open('./templates/create_wiki.html').read()
# j2s.setup(app,loader=DictLoader(template_dict))

# Create async mongo connection
# Make motor-mongo use the same event loop as sanic
# @app.listener('before_server_start')
# def setup_db(app,loop):
#     app.db = AsyncIOMotorClient(app.config['MONGOURI'])['paperwiki']

@app.route("/", methods=['GET', 'POST'])
def home():
    resp = render_template("home.html")
    return resp

async def do_find_one(clusterID):
    document = await app.db.paperwiki.find_one({'clusterID': clusterID})
    return document

@app.route("/search", methods=['GET','POST'])
def search():
    """
    Uses Crossref API to search documents.
    """
    queries = {}
    for key in ['author','words','doi']:
        val = request.form[key]
        if len(val)>0:
            queries[key] = request.form[key]
        else:
            queries[key] = None
    # Init API and query
    works = Works()
    articles_q = []
    if queries['doi']:
        articles_q = [works.doi(doi = queries['doi'])]
    else:
        articles_q = works.query(bibliographic=queries['words'], author=queries['author']).sample(20)
    # Check if article is in database already and wiki exists
    articles = []
    for article in articles_q:
        articles.append(article)
        doi = article['DOI']
        search_result = mongo.db.paperwiki.find_one({ "DOI" : doi})
        if search_result:
            if 'content' in search_result.keys():
                article['actionurl'] = "see_wiki?id=" + doi
                article['wiki_exists'] = True
            else:
                article['actionurl'] = "create_wiki?id=" + doi
                article['wiki_exists'] = False
        else:
            insert_id = mongo.db.paperwiki.insert_one(article)
            article['actionurl'] = "create_wiki?id=" + doi
            article['wiki_exists'] = False
    context = {"docs":articles}
    resp = render_template("home.html",docs=articles)
    return resp

@app.route("/create_wiki", methods=['GET','POST'])
@app.route('/create_wiki/<id>')
def create_wiki(id=None):
    """
    Create new wiki page
    """
    clusterID = str(request.form['create_wiki'])
    submit_url = "submit_wiki?id=" + clusterID
    doc = mongo.db.paperwiki.find_one({ "DOI" : clusterID})
    context={"cluster_id":request.form['create_wiki']}
    form = PageDownFormExample()
    if form.validate_on_submit():
        text = form.pagedown.data
    if 'content' not in doc.keys():
        doc['content'] = "Add information about article here!"
    resp = render_template("create_wiki.html", id = clusterID, submit_url=submit_url, form = form,doc=doc)
    return resp

@app.route("/submit_wiki", methods=['GET','POST'])
@app.route('/submit_wiki/<id>')
def submit_wiki(id=None):
    """
    Submit new or modified wiki page
    """
    # print(request.form['submit_wiki'])
    clusterID = str(request.args.get('id'))
    response = json.loads(request.form['submit_wiki'])
    search_result = mongo.db.paperwiki.find_one({ "DOI" : clusterID})
    search_result['content'] = str(response['content'])
    insert_id = mongo.db.paperwiki.replace_one({'_id':search_result['_id']},search_result) # mongo
    content = Markup(markdown.markdown(search_result['content']))
    search_result['actionurl'] = "edit_wiki?id=" + clusterID
    resp = render_template("see_wiki.html",id=clusterID,doc=search_result,content=content)
    return resp

@app.route("/see_wiki", methods=['GET','POST'])
@app.route('/see_wiki/<id>')
def see_wiki(id=None):
    """
    See existing wiki page
    """
    clusterID = str(request.args.get('id'))
    search_result = mongo.db.paperwiki.find_one({ "DOI" : clusterID})
    content = Markup(markdown.markdown(search_result['content']))
    search_result['actionurl'] = "edit_wiki?id=" + clusterID
    resp = render_template("see_wiki.html",id=clusterID,doc=search_result,content=content)
    return resp

@app.route("/edit_wiki", methods=['GET','POST'])
@app.route('/edit_wiki/<id>')
def edit_wiki(id=None):
    """
    Edit existing wiki page
    """
    print("now in edit wiki")
    clusterID = str(request.args.get('id'))
    print(clusterID)
    search_result = mongo.db.paperwiki.find_one({ "DOI" : clusterID})
    content = Markup(markdown.markdown(search_result['content']))
    search_result['content'] = search_result['content']
    search_result['actionurl'] = "submit_wiki?id=" + clusterID
    form = PageDownFormExample()
    if form.validate_on_submit():
        text = form.pagedown.data
    print(content)
    resp = render_template("edit_wiki.html",id=clusterID, doc=search_result, form = form)
    return resp

ON_HEROKU = os.environ.get('ON_HEROKU')

if ON_HEROKU:
    # get the heroku port
    port = int(os.environ.get('PORT', 17995))  # as per OP comments default is 17995
else:
    port = 5000

if __name__ == "__main__":
    print("Running on Port 5000")
    # Can change workers to num cores for better performance
    app.run(host="0.0.0.0",port=port,debug=True)

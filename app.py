# App from sanic
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms.fields import SubmitField
from flask_pagedown import PageDown

class PageDownFormExample(FlaskForm):
    pagedown = PageDownField('Enter your markdown')
    submit = SubmitField('Submit')

# Handle mongo queries async style
# from motor.motor_asyncio import AsyncIOMotorClient

# Template rendering
# from jinja2 import DictLoader
# import jinja2_sanic as j2s
# External async connections
import asyncio
import uvloop
# Utils
import os, subprocess, threading
import json
from sanic.response import json
from datetime import datetime

# Scholar searcher.
from scholar import SearchScholarQuery, ScholarQuerier, SearchScholarQuery,ScholarSettings

# Create app
app = Flask(__name__)
pagedown = PageDown(app)
app.config.from_pyfile('./config.py')
app.config.update(dict(
    SECRET_KEY="powerful secretkey",
    WTF_CSRF_SECRET_KEY="a csrf secret key"
))
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

@app.route("/search", methods=['GET','POST'])
def search():
    """
    Uses scholar.py to read documents from google search.

    """
    author = request.form['author']
    words = request.form['words']
    querier = ScholarQuerier()
    query = SearchScholarQuery()
    settings = ScholarSettings()
    settings.set_citation_format(ScholarSettings.CITFORM_BIBTEX)
    querier.apply_settings(settings)
    query.set_author(author)
    query.set_words(words)
    # Queries Google Scholar
    querier.send_query(query)
    # Parse results
    articles = []
    for article in querier.articles:
        article = article.attrs
        # Add check DB if wiki exists. Add attribute wiki_exists
        if True:
            article['wiki_exists'] = True
        else:
            article['wiki_exists'] = False
        articles.append(article)
    context = {"docs":articles}
    resp = render_template("home.html",docs=articles)
    return resp

@app.route("/create_wiki", methods=['GET','POST'])
def create_wiki():
    """
    Create new wiki page
    """
    print(request.form['create_wiki'])
    context={"cluster_id":request.form['create_wiki']}
    form = PageDownFormExample()
    if form.validate_on_submit():
        text = form.pagedown.data
    resp = render_template("create_wiki.html",form = form)
    return resp

@app.route("/see_wiki", methods=['GET','POST'])
def see_wiki():
    """
    See existing wiki page
    """
    print(request.form['see_wiki'])
    context={"cluster_id":request.form['see_wiki']}
    resp = render_template("see_wiki.html")
    return resp

if __name__ == "__main__":
    print("Running on Port 5000")
    # Can change workers to num cores for better performance
    app.run(host="0.0.0.0",port=5000)

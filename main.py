#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# To clear the local datastore:
# https://cloud.google.com/appengine/docs/python/tools/devserver

import os
import re
import json
import codecs
import urllib
import jinja2
import webapp2
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb


# Set up the API key
fh = open('secret.json', 'rU')
API_KEY = json.loads(fh.read())['api_key']
fh.close()


jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)


# We give the models an ancestor so they all stay in one entity group.
# This is the function we use to retrieve that key.
ANCESTOR_KEY = ndb.Key(u'ArticleAncestor', 'AA')

# How many articles we get each fetch.
NITEMS_PER_FETCH = 10


def get_sports_articles(page=0):
    """Makes a request to the New York Times article API.

    Parameters
    ----------
    page: int
        A non-negative integer.

    Returns
    -------
    A list of article items.
    """
    if page < 0:
        page = 0

    url = 'http://api.nytimes.com/svc/search/v2/articlesearch.json?' + \
            'fq=news_desk:("Sports")&sort=newest&page={}&api-key={}'.format(page, API_KEY)
    s = urllib.urlopen(url)
    result = json.loads(s.read())
    if result['status'] == 'OK':
        # we are looking to use the subsection_name, snippet, headline, and multimedia
        # field of the items in the response list.
        return result['response']['docs']
    return []


def make_article_json(a):
    """Make an Article object into a dictionary."""
    j = {
        'snippet': a.snippet,
        'aid': a.aid
    }
    if a.subsection_name:
        j['subsection_name'] = a.subsection_name
    if a.imgurl:
        j['imgurl'] = a.imgurl
    return j
    

class Article(ndb.Model):
    """This is our data model."""
    
    # The id field from NYTimes. We use this to check if there is any
    # repetition.
    nytid = ndb.StringProperty()
    
    # Not exactly a URL. This is the path to the image under NYTimes' domain.
    imgurl = ndb.StringProperty(required=False)
    
    # What sport it is. Not guaranteed to be provided.
    subsection_name = ndb.StringProperty(required=False)
    
    snippet = ndb.TextProperty()
    
    # The article ID. We maintain this field so that is saves us a lot of
    # trouble comparing dates.
    aid = ndb.IntegerProperty()
    
    @classmethod
    def make_ancestor_query(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.aid)


class MainPage(webapp2.RequestHandler):
    def get(self):
        ctx = {}
        template = jinja_env.get_template('index.html')
        self.response.out.write(template.render(ctx))

        
class LoadArticlesHandler(webapp2.RequestHandler):
    def get(self):
        q = Article.make_ancestor_query(ANCESTOR_KEY)
        s = self.request.get('s')
        b = self.request.get('b')
        if len(s):
            try:
                s = int(s)
            except ValueError:
                self.response.set_status(
                        code=400, 
                        message='Invalid parameters.')
                return
            q = q.filter(Article.aid < s)
        if len(b):
            try:
                b = int(b)
            except ValueError:
                self.response.set_status(
                        code=400, 
                        message='Invalid parameters.')
                return
            q = q.filter(Article.aid > b)
        
        articles = q.fetch(NITEMS_PER_FETCH)
        resp = {
            'data': [make_article_json(x) for x in articles]
        }
        if not b and len(resp['data']) < NITEMS_PER_FETCH:
            # there are no more articles to fetch
            resp['more'] = False
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(resp))        


class CronUpdateHandler(webapp2.RequestHandler):
    def get(self):
        articles = get_sports_articles()
        
        n, latest_nytid = 0, None
        latest = Article.make_ancestor_query(ANCESTOR_KEY).get()
        if latest:
            n = latest.aid
            latest_nytid = latest.nytid
        
        # Check if there is any articles we already recorded    
        if latest_nytid is not None:
            repeat_from_idx = None
            for i in xrange(len(articles)):
                if articles[i]['_id'] == latest_nytid:
                    repeat_from_idx = i
                    break
            if repeat_from_idx is not None:
                articles = articles[:repeat_from_idx]
        
        # Update the new articles to the data store
        # Make sure we insert the older ones first
        for a in reversed(articles):
            n += 1
            new_article = Article(parent=ANCESTOR_KEY)
            new_article.nytid = a['_id']
            new_article.snippet = a['snippet']
            if len(a['multimedia']):
                new_article.imgurl = a['multimedia'][1]['url']
            if 'subsection_name' in a:
                new_article.subsection_name = a['subsection_name']
            new_article.aid = n
            new_article.put()
            
        self.response.out.write('cron jobs ok')
        

       
routes = [    
        webapp2.Route('/', handler=MainPage),
        webapp2.Route('/articles', handler=LoadArticlesHandler),
        webapp2.Route('/tasks/update', handler=CronUpdateHandler),
        ]

# turn off the debug switch
app = webapp2.WSGIApplication(routes, debug=False)


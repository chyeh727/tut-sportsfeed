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


# Sets up the API key
fh = open('secret.json', 'rU')
API_KEY = json.loads(fh.read())['api_key']
fh.close()


jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)


# Load dummy data. This is to be removed in the live version.
fh = open('dummydata.json', 'rU')
dummy_data = json.loads(fh.read())
fh.close()


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


class MainPage(webapp2.RequestHandler):
    def get(self):
        ctx = {}
        template = jinja_env.get_template('index.html')
        self.response.out.write(template.render(ctx))

        
class LoadArticlesHandler(webapp2.RequestHandler):
    def get(self):
        resp = dummy_data
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(resp))        

        
class AjaxRequestHandlerExample(webapp2.RequestHandler):
    def get(self):
        resp = {}
        ccode = self.request.get('ccode')
        aid = int(self.request.get('aid'))

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(resp))

       
routes = []
##### Add your new handler here (begin) #####

routes.append(webapp2.Route('/', handler=MainPage))
routes.append(webapp2.Route('/articles', handler=LoadArticlesHandler))
#routes.append(webapp2.Route('/ajax', handler=AjaxRequestHandlerExample))

##### Add your new handler here (end) #####

# turn off the debug switch
app = webapp2.WSGIApplication(routes, debug=False)


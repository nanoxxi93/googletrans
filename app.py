"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, jsonify, request, url_for, render_template
from flask import render_template, Blueprint, make_response
from urllib import request as rq
from googletrans import Translator
import logging
import datetime
import json

app = Flask(__name__)
#app.debug = True

class PrefixMiddleware(object):
#class for URL sorting 
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        #in this line I'm doing a replace of the word flaskredirect which is my app name in IIS to ensure proper URL redirect
        if environ['PATH_INFO'].lower().replace('/translator','').startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'].lower().replace('/translator','')[len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])            
            return ["This url does not belong to the app.".encode()]

# Make the WSGI interface available at the top level so wfastcgi can get it.
# wsgi_app = app.wsgi_app
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')

logging.basicConfig(filename='log.log',level=logging.DEBUG,format='%(asctime)s - %(process)d-%(levelname)s-%(message)s')

def detect(text):
    try:
        logging.debug('Text: {}'.format(text))
        translator = Translator()
        language = translator.detect(text)
        logging.debug('Language: {}'.format(language))
        return language.lang
    except Exception as e:
        logging.exception('Error: {} '.format(e))
        raise(e)

def translate(text, source, target):
    try:
        logging.debug('Text: {}'.format(text))
        translator = Translator()
        if source is not None or target is not None:
            logging.debug('{} -> {}'.format(source, target))
        if source is None and target is None:
            translation = translator.translate(text)
        elif source is None:
            translation = translator.translate(text, dest=target)
        elif target is None:
            translation = translator.translate(text, src=source)
        else:
            translation = translator.translate(text, src=source, dest=target)
        logging.debug('Translation: {}'.format(translation))
        return translation.text
    except Exception as e:
        logging.exception('Error: {} '.format(e))
        raise(e)

@app.route('/detect', methods=['GET','POST'])
def detectController():
    try:
        if (request.method == 'POST'):
            some_json = request.get_json() # request -> json
            text = some_json['text']
            result = detect(text)
        elif (request.method == 'GET'):
            result = 'Envíe un POST con "text"'
        return jsonify(result), 200
    except Exception as e:
        logging.exception('Exception occurred {}'.format(e))
        return jsonify(str(e)), 401

@app.route('/translate', methods=['GET','POST'])
def translateController():
    try:
        if (request.method == 'POST'):
            some_json = request.get_json() # request -> json
            text = some_json['text']
            source = some_json.get('source', None)
            target = some_json.get('target', None)
            result = translate(text, source, target)
        elif (request.method == 'GET'):
            result = 'Envíe un POST con "text", "source" y "target"'
        return jsonify(result), 200
    except Exception as e:
        logging.exception('Exception occurred {}'.format(e))
        return jsonify(str(e)), 401

@app.route('/values')
def valuesController():
    return jsonify({'about':'FLASK API REST RUNNING'})

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8083)
    #app.run(host='0.0.0.0')
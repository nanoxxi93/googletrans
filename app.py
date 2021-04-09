import json
from flask import Flask, jsonify, request, url_for, render_template
from flask import render_template, Blueprint, make_response
import logging
from logdna import LogDNAHandler
import datetime
from urllib import request as rq
from googletrans import Translator

app = Flask(__name__)

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

ingestionKey = 'b7c813e09f26938d8bcd7c4f38be2a40'
logdna_options = {
  'app': 'googletrans',
  'level': 'Debug',
  'index_meta': True
}
logging.basicConfig(
    handlers=[
        logging.FileHandler(filename='log.log', encoding='utf-8', mode='a+'),
        LogDNAHandler(ingestionKey, logdna_options)
    ],
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y%m%d.%H%M%S'
)

def fn_detect(text):
    fnc = 'fn_detect'
    try:
        if not (type(text) == str and text != ''):
            raise TypeError('text should be a string')
        logging.debug('{} --> Text: {}'.format(fnc, text))
        translator = Translator()
        language = translator.detect(text)
        logging.debug('{} --> Language: {}'.format(fnc, language))
        return language.lang
    except Exception as e:
        raise e

def fn_translate(text, source, target):
    fnc = 'fn_translate'
    try:
        if not (type(text) == str and text != ''):
            raise TypeError('text should be a string')
        logging.debug('{} --> Text: {}'.format(fnc, text))
        logging.debug('{} --> Model: {}-{}'.format(fnc, source, target))
        translator = Translator()
        if source is not None or target is not None:
            pass
        if source is None and target is None:
            translation = translator.translate(text)
        elif source is None:
            translation = translator.translate(text, dest=target)
        elif target is None:
            translation = translator.translate(text, src=source)
        else:
            translation = translator.translate(text, src=source, dest=target)
        logging.debug('{} --> Translation: {}'.format(fnc, translation))
        return translation.text
    except Exception as e:
        raise e

@app.route('/detect', methods=['GET','POST'])
def detect_controller():
    endpoint = request.endpoint
    try:
        if (request.method == 'POST'):
            if (request.is_json):
                request_json = request.get_json() # request -> json
                logging.debug('{} --> REQUEST: {}'.format(endpoint, json.dumps(request_json)))
                text = request_json['text']
                result = fn_detect(text)
                logging.info('{} --> RESULT: {}'.format(endpoint, result))
                return jsonify(result), 200
            else:
                raise TypeError('The body is not a valid json')
        else:
            return 'Method not allowed', 400
    except KeyError as e:
        logging.exception(e)
        return '{} parameter not found'.format(str(e)), 400
    except (AssertionError, TypeError, ValueError) as e:
        logging.exception(e)
        return str(e), 400
    except Exception as e:
        logging.exception(e)
        return 'Please contact with support', 400

@app.route('/translate', methods=['GET','POST'])
def translate_controller():
    endpoint = request.endpoint
    try:
        if (request.method == 'POST'):
            if (request.is_json):
                request_json = request.get_json() # request -> json
                logging.debug('{} --> REQUEST: {}'.format(endpoint, json.dumps(request_json)))
                text = request_json['text']
                source = request_json.get('source', None)
                target = request_json.get('target', None)
                result = fn_translate(text, source, target)
                logging.info('{} --> RESULT: {}'.format(endpoint, result))
                return jsonify(result), 200
            else:
                raise TypeError('The body is not a valid json')
        else:
            return 'Method not allowed', 400
    except KeyError as e:
        logging.exception(e)
        return '{} parameter not found'.format(str(e)), 400
    except (AttributeError, AssertionError, TypeError, ValueError) as e:
        logging.exception(e)
        return str(e), 400
    except Exception as e:
        logging.exception(e)
        return 'Please contact with support', 400

@app.route('/values')
def values_controller():
    return 'Api is running'

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8083) # waitress-serve --port=8083 app:app
    # app.run(host='0.0.0.0') # flask run
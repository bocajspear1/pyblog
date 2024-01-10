import importlib
import os
import sys
import json
from datetime import datetime

from flask import Flask, g, jsonify, current_app, request, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth

import markdown

class MySQLDatastore():
    pass

class RedisDatastore():

    def __init__(self, host):
        import redis
        self._r = redis.Redis(host=host, port=6379, decode_responses=True)

    def get_article_data(self, filename):

        tags = self._r.get(f"{filename}-tags")
        if tags is None:
            tags = []
        else:
            tags = tags.split(",")
            
        pinned = self._r.get(f"{filename}-pinned")
        print(pinned)
        if pinned and int(pinned) == 1:
            pinned = True
        else:
            pinned = False

        ret_item = {
            "title": self._r.get(f"{filename}-title"),
            "description": self._r.get(f"{filename}-description"),
            "tags": tags,
            "pinned": pinned
        }

        return ret_item
    
    def set_article_data(self, filename, title, description, tags, pinned):
        self._r.set(f"{filename}-title", title),
        self._r.set(f"{filename}-description", description),
        self._r.set(f"{filename}-tags", ",".join(tags))
        if pinned:
            pinned = 1
        else:
            pinned = 0
        self._r.set(f"{filename}-pinned", pinned)
        

def create_func(app, plugin_name, plugin):
    def temp_func():
        return plugin.call(app, request)
    temp_func.__name__ = plugin_name
    return temp_func

def get_article_content(filename):
    root_dir = os.path.dirname(__file__)
    file_path = os.path.join(root_dir, "articles", filename)
    file_ptr = open(file_path, "r")
    file_data = file_ptr.read()
    file_ptr.close()
    return file_data

def set_article_content(filename, content):
    root_dir = os.path.dirname(__file__)
    file_path = os.path.join(root_dir, "articles", filename)
    file_ptr = open(file_path, "w")
    file_ptr.write(content)
    file_ptr.close()

def get_pinned_list(datastore):
    root_dir = os.path.dirname(__file__)
    article_list = os.listdir(os.path.join(root_dir, 'articles'))

    final_list = []

    for article_item in article_list:
        article_data = datastore.get_article_data(article_item)
        print(article_item, article_data)
        if article_data['pinned']:
            final_list.append({
                "filename": article_item,
                "title": article_data['title']
            })
    
    return final_list

def create_server():

    app = Flask(__name__)
    auth = HTTPBasicAuth()
    app.secret_key = '12345678'

    with app.app_context():
      
        root_dir = os.path.dirname(__file__)

        config_file = open(os.path.join(root_dir, "config.json"), "r")
        config_json = json.load(config_file)
        config_file.close()

        app._config = config_json

        if app._config['db_type'] == "redis":
            app._datastore = RedisDatastore(app._config['db_host'])


        plugin_list = os.listdir(os.path.join(root_dir, 'plugins'))

        sys.path.append(root_dir)

        for plugin in plugin_list:
            if plugin.endswith(".py"):
                temp = importlib.import_module("plugins." + plugin.replace(".py", ""))
                temp_module = temp.__PLUGIN__()

                temp_func = create_func(app, temp_module.__class__.__name__, temp_module)
                app.route(temp_module.URI, methods = ['GET', 'POST'])(temp_func)
        
        @auth.verify_password
        def verify_password(username, password):
            if username == app._config['username'] and password == app._config['password']:
                return username

        @app.route('/', methods = ['GET'])
        def home():

            pinned_list = get_pinned_list(app._datastore)

            if 'page' in request.args and request.args['page'] is not None:
                file_data = get_article_content(request.args['page'])
                article_data = app._datastore.get_article_data(request.args['page'])

                if request.args['page'].endswith(".md"):
                    
                    file_data = markdown.markdown(file_data)

                return render_template("home.html", page_name=article_data['title'], content=file_data, filename=request.args['page'], pinned_list=pinned_list)
            else:

                article_list = os.listdir(os.path.join(root_dir, 'articles'))

                final_list = []



                for article_item in article_list:
                    last_modified_time = os.path.getmtime(os.path.join(root_dir, "articles", article_item))

                    article_data = app._datastore.get_article_data(article_item)

                    if 'tag' in request.args:
                        if request.args['tag'] not in article_data['tags']:
                            continue


                    final_list.append({
                        "filename": article_item,
                        "title": article_data['title'],
                        "description": article_data['description'],
                        "tags": article_data['tags'],
                        "last_updated": datetime.fromtimestamp(last_modified_time).isoformat()
                    })

                sorted_list = sorted(final_list, key=lambda d: d['last_updated'], reverse=True) 

                offset = 0

                if 'offset' in request.args:
                    offset = int(request.args['offset'])-1

                count = 10
                return render_template("home.html", page_name="Home", article_list=sorted_list[offset*count:(offset*count)+count], 
                                       pinned_list=pinned_list, total_pages=int(len(sorted_list)/count))
        
        @app.route('/edit', methods = ['GET', 'POST'])
        @auth.login_required
        def edit():
            if request.method == 'POST':
                print(request.form)
                filename = request.form.get("filename", "")
                title = request.form.get("title", "")
                description = request.form.get("description", "")
                tags = request.form.get("tags", "").split(",")
                content = request.form.get("content", "")
                pinned = request.form.get("pinned", "off")
                if pinned == "on":
                    pinned = True
                else:
                    pinned = False

                set_article_content(filename, content)

                app._datastore.set_article_data(filename, title, description, tags, pinned)

                return render_template("edit.html", filename=filename, 
                                           title=title,
                                           description=description,
                                           tags=",".join(tags),
                                           content=content,
                                           pinned=pinned
                                          )
                
            elif request.method == 'GET':
                if 'page' in request.args:
                    article_data = app._datastore.get_article_data(request.args['page'])
                    file_data = get_article_content(request.args['page'])

                    return render_template("edit.html", filename=request.args['page'], 
                                           title=article_data['title'],
                                           description=article_data['description'],
                                           tags=",".join(article_data['tags']),
                                           content=file_data,
                                           pinned=article_data['pinned']
                                          )
                else:
                    return render_template("edit.html")
        
    return app



if __name__== '__main__':
    create_server().run(debug=True)
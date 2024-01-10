from io import StringIO
import sys

from flask import render_template

class EvalModule():

    URI = "/eval"

    def __init__(self):
        pass

    def call(self, app, request):
        if request.method == "GET":
            return render_template("eval.html")
        else:
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            eval(request.form['code'])

            sys.stdout = old_stdout

            return render_template("eval.html", output=mystdout.getvalue())

__PLUGIN__ = EvalModule
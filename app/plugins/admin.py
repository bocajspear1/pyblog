
import os
import subprocess

from flask import render_template
import psutil

class AdminModule():

    URI = "/admin"

    def __init__(self):
        pass

    def call(self, app, request):

        memory_percent = round((psutil.virtual_memory().available * 100 / psutil.virtual_memory().total), 2)

        command = "ps aux"

        if 'filter' in request.args:
            command += " | grep " + request.args['filter']

        ps_proc = subprocess.run(command, shell=True, capture_output=True)


        return render_template("admin.html", cpu=psutil.cpu_percent(0.1), memory=memory_percent, ps_list=ps_proc.stdout.decode())

__PLUGIN__ = AdminModule
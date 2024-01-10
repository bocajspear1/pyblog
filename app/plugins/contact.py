

from flask import render_template


class ContactModule():

    URI = "/contact"

    def __init__(self):
        pass

    def call(self, app, request):
        return render_template("contact.html")

__PLUGIN__ = ContactModule
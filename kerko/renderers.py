from abc import ABC, abstractmethod

from flask import render_template, render_template_string


class Renderer(ABC):

    @abstractmethod
    def render(self, **context):
        pass


class TemplateRenderer:

    def __init__(self, template):
        self.template = template

    def render(self, **context):
        return render_template(self.template, **context)


class TemplateStringRenderer:

    def __init__(self, template_string):
        self.template_string = template_string

    def render(self, **context):
        return render_template_string(self.template_string, **context)

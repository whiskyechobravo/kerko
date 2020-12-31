import re
from abc import ABC, abstractmethod

from flask import render_template, render_template_string


class Renderer(ABC):

    @abstractmethod
    def render(self, **context):
        pass


class TemplateRenderer:
    """Render using a template file."""

    def __init__(self, template, **extra_context):
        self.template = template
        self.extra_context = extra_context

    def render(self, **context):
        return render_template(self.template, **context, **self.extra_context)


class TemplateResolverRenderer:
    """Render using a template file whose name is resolved from context."""

    def __init__(self, template, **extra_context):
        """
        Initialize the object.

        :param str template: A template name with replacement fields delimited
            with braces (i.e. à la `str.format`). Those will be replaced at
            rendering time with values from context to determine the template
            name.
        """
        self.template = template
        self.extra_context = extra_context
        self.fields = re.findall(r'\{(.*?)\}', self.template)

    def render(self, **context):
        return render_template(
            self.template.format(**{kw: context[kw] for kw in self.fields if kw in context}),
            **context, **self.extra_context
        )


class TemplateStringRenderer:
    """Render using a template string."""

    def __init__(self, template_string, **extra_context):
        self.template_string = template_string
        self.extra_context = extra_context

    def render(self, **context):
        return render_template_string(self.template_string, **context, **self.extra_context)

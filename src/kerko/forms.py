from flask_wtf import FlaskForm
from wtforms import SelectField, validators
from wtforms.fields.html5 import SearchField

from kerko.shortcuts import composer


class SearchForm(FlaskForm):
    scope = SelectField()
    keywords = SearchField(validators=[validators.optional(), validators.length(max=1000)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scope.choices = [
            (s.key, s.selector_label)
            for s in composer().get_ordered_specs('scopes')
        ]

from wtforms import SelectField, validators
from wtforms.fields.html5 import SearchField

from flask import current_app
from flask_wtf import FlaskForm


class SearchForm(FlaskForm):
    scope = SelectField()
    keywords = SearchField(validators=[validators.optional(), validators.length(max=1000)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scope.choices = [
            (s.key, s.selector_label)
            for s in current_app.config['KERKO_COMPOSER'].get_ordered_specs('scopes')
        ]

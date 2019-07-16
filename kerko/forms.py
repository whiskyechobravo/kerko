from wtforms import SelectField
from wtforms.fields.html5 import SearchField

from flask import current_app
from flask_wtf import FlaskForm


class SearchForm(FlaskForm):
    scope = SelectField()
    keywords = SearchField()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scope.choices = [
            (s.key, s.selector_label)
            for s in current_app.config['KERKO_COMPOSER'].get_ordered_scopes()
        ]

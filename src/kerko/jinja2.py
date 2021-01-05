"""
Custom filters for Jinja2 templates.
"""

from .datetime import format_datetime, reformat_date


def register_filters(blueprint):
    """Add custom template filters."""
    blueprint.add_app_template_filter(format_datetime, name='kerko_format_datetime')
    blueprint.add_app_template_filter(reformat_date, name='kerko_reformat_date')

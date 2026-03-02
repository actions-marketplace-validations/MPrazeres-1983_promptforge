"""Jinja2-based prompt template rendering."""

from __future__ import annotations

from jinja2 import Environment, StrictUndefined, TemplateError

from promptforge.core.errors import PromptSpecError


_env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)


def render_template(template: str, inputs: dict) -> str:
    """Render a Jinja2 template with the given inputs.

    Raises PromptSpecError if a variable is missing or template is invalid.
    """
    try:
        tmpl = _env.from_string(template)
        return tmpl.render(**inputs)
    except TemplateError as e:
        raise PromptSpecError(f"Template rendering error: {e}") from e
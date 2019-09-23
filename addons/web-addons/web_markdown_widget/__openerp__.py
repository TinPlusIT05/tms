# -*- coding: utf-8 -*-
{
    "name": 'web_markdown_widget',
    "category": 'Web',
    "version": "0.1",
    "description":"""
=====================================================================================
Markdown support for text field with highlight syntax and [tab] indentation support.
=====================================================================================

+ For more information about syntax highlight and basic markdown for use, please checkout the links below:

    + Basic Markdown:
        - https://help.github.com/articles/markdown-basics

    + GitHub Flavored Markdown:
        - https://help.github.com/articles/github-flavored-markdown

    + More Markdown Example:
        - https://guides.github.com/features/mastering-markdown/

    + Markdown Cheatsheet (with syntax highlight detection):
        - https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet

+ Current version supports markdown for text field on form view and list view.

+ To use markdown widget, just put the following to you field code:

    widget="markdown"

+ Full example:

    <field name="your_text_field_name" widget="markdown" />
    """,
    "depends": [
        'base', 'web_unleashed'
    ],
    "data": [
        'views/web_markdown_widget.xml',
    ],
    "qweb":[
        'static/src/xml/template.xml',
    ],
    "css": [],
    "js": [],
    "author": "Trobz",
    "installable" : True,
    "active" : False,
}
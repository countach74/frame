#!/usr/bin/python

from setuptools import setup

setup(
	name="frame",
	version="0.0.1",
	author="Tim Radke",
	author_email="countach74@gmail.com",
	description="A very simple, lightweight MVC-based web framework.",
	license="GNU",
	keywords="web framework mvc",
	packages=['frame', 'frame.server', 'frame.orm'],
	package_data={'frame': ['templates/*.html', 'templates/errors/*.html', 'templates/forms/*.html', 'templates/forms/elements/*.html']},
	install_requires=['Jinja2', 'Flup', 'Routes', 'python-memcached']
)

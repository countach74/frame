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
	packages=['frame', 'frame.server'],
	package_data={'frame': ['templates/*.html', 'templates/errors/*.html']},
	install_requires=['Jinja2']
)

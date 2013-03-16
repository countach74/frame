#!/usr/bin/python

from setuptools import setup

setup(
	name="frame",
	version="0.1a",
	author="Tim Radke",
	author_email="countach74@gmail.com",
	description="A very simple, lightweight MVC-based web framework.",
	license="GNU",
	keywords="web framework mvc",
	packages=[
		'frame',
		'frame.server',
		'frame.orm',
		'frame.orm.drivers',
		'frame.orm.drivers.mongo',
		'frame.testsuite',
	],
	package_data={
		'frame': [
			'templates/*.html',
			'templates/includes/*.html',
			'templates/errors/*.html',
			'templates/forms/*.html',
			'templates/forms/elements/*.html',
			'templates/forms/includes/*.html',
			'templates/macros/*.html',
			'templates/js/*.js',
			'static/js/*.js',
			'static/css/*.css',
			'testsuite/templates/*.html',
			'testsuite/templates/controller/*.html',
		]
	},
	install_requires=['Jinja2', 'Routes', 'pytz']
)

#!/usr/bin/python

from setuptools import setup

setup(
  name="frame",
  version="0.3.1",
  author="Tim Radke",
  author_email="countach74@gmail.com",
  description="A very simple, lightweight MVC-based web framework.",
  license="GNU",
  keywords="web framework mvc",
  packages=[
    'frame',
    'frame.server',
    'frame.extensions',
    'frame.testsuite',
  ],
  entry_points={
    'frame.drivers': [
      'session = frame.extensions.sessions:register_driver',
      'templates = frame.extensions.templates:register_driver[templates]',
      'jade = frame.extensions.jade:register_driver[jade]'
    ],
    'frame.config': [
      'session = frame.extensions.sessions:register_config',
      'templates = frame.extensions.templates:register_config[templates]',
      'jade = frame.extensions.jade:register_config[jade]'
    ]
  },
  extras_require={
    'templates': [],
    'jade': ['pyjade']
  },
  package_data={
    'frame': [
      'templates/*.html',
      'templates/includes/*.html',
      'templates/__errors/*.html',
      'templates/__errors/jinja2/*.html',
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
  install_requires=['Jinja2', 'Routes', 'pytz', 'multipart']
)

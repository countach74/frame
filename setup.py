#!/usr/bin/env python

from setuptools import setup

setup(
  name="frame",
  version="0.3.2",
  author="Tim Radke",
  author_email="countach74@gmail.com",
  description="A very simple, lightweight MVC-based web framework.",
  url="http://github.com/countach74/frame",
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
    ],
    'frame.config': [
      'session = frame.extensions.sessions:register_config',
      'templates = frame.extensions.templates:register_config[templates]',
    ]
  },
  extras_require={
    'templates': ['jinja2']
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
  install_requires=['Routes', 'pytz', 'multipart']
)

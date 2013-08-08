from frame.extensions.templates import Jinja2Driver, TemplateDriver
from frame.dotdict import DotDict
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader


jade_config = DotDict({
  'loaders': [
    PackageLoader('frame', 'templates')
  ],
  'extensions': [],
  'suffix': '.jade',
  'directory': 'templates'
})


class JadeDriver(Jinja2Driver):
  def __init__(self, **options):
    TemplateDriver.__init__(self, **options)

    loaders = list(jade_config.loaders + options['loaders'])
    loaders.insert(0, FileSystemLoader(jade_config.directory))

    self.environment = Environment(
      loader=ChoiceLoader(loaders),
      extensions=jade_config.extensions + ['pyjade.ext.jinja.PyJadeExtension'])


def register_config(config):
  config.templates.jade = jade_config


def register_driver(drivers):
  drivers.register('template', 'jade', JadeDriver)

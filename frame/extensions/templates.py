from ..driverinterface import DriverInterface
from ..dotdict import DotDict
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader
from abc import ABCMeta, abstractmethod, abstractproperty
import os
from .. import errors


templates_config = DotDict({
  'driver': 'jinja2',
  'globals': {},
  'filters': {},
  'jinja2': {
    'environment': None
  },
  'loaders': [PackageLoader('frame', 'templates')],
  'directory': 'templates',
  'suffix': '.html',
  'extensions': ['jinja2.ext.do']
})


class TemplateDriver(object):
  __metaclass__ = ABCMeta
  def __init__(self, **options):
    self.options = options

  @abstractmethod
  def get_template(self, template, variables={}):
    '''
    Return the requested template with the variables
    '''
    pass

  @abstractproperty
  def globals(self):
    pass

  @abstractproperty
  def filters(self):
    pass

  @abstractmethod
  def render(self, template, data):
    pass


class Jinja2Driver(TemplateDriver):
  def __init__(self, **options):
    TemplateDriver.__init__(self, **options)

    loaders = list(options['loaders'])
    loaders.insert(0, FileSystemLoader(options['directory']))

    if templates_config.jinja2.environment:
      self.environment = templates_config.jinja2.environment
    else:
      self.environment = Environment(
        loader=ChoiceLoader(loaders),
        extensions=options['extensions'])

  def render(self, template, data):
    return self.environment.get_template(template).render(**data)

  def get_template(self, *args, **kwargs):
    return self.environment.get_template(*args, **kwargs)

  @property
  def globals(self):
    return self.environment.globals

  @property
  def filters(self):
    return self.environment.filters


class TemplateInterface(DriverInterface):
  def __init__(self, *args, **kwargs):
    from .. import _app
    self.app = _app.app
    DriverInterface.__init__(self, *args, **kwargs)

  def init(self, driver, **options):
    driver_object = driver(**options)

    for k, v in templates_config.globals.iteritems():
      driver_object.globals[k] = v

    for k, v in templates_config.filters.iteritems():
      driver_object.filters[k] = v

    return driver_object

  def get_template(self, *args, **kwargs):
    return self.app.template_engine.get_template(*args, **kwargs)

  @property
  def globals(self):
    return self.app.template_engine.globals

  @property
  def filters(self):
    return self.app.template_engine.filters



class TemplateHook(object):
  priority = 100

  def __init__(self, app, controller):
    self.app = app
    self.controller = controller

  def __enter__(self):
    self.controller.get_template = self.app.drivers.template.current.get_template

  def __exit__(self, e_type, e_value, e_tb):
    pass


def templatize(request, response):
  if isinstance(response.body, dict) or response.body is None:
    class_name = response.action.im_class.__name__
    action_name = response.action.__name__

    template_path = os.path.join(
      class_name.lower(),
      action_name + templates_config.suffix
    )   

    try:
      response.body = response.app.template_engine.render(
        template_path, response.body or {})
    except Exception, e:
      return errors.Error500().response

templatize.priority = 50


original_HTTPError_setup_response = errors.Error500.setup_response


def HTTPError_setup_response(self, status, headers, body):
  from .. import response
  import jinja2
  from .._app import app

  split = status.split(None, 1)
  self.kwargs['app'] = app
  self.kwargs['status'] = status

  if not body:
    try:
      body = app.template_engine.render('__errors/jinja2/%s.html' % split[0],
        self.kwargs)
    except jinja2.exceptions.TemplateNotFound:
      body = app.template_engine.render('__errors/jinja2/generic.html',
        self.kwargs)
    except Exception, e:
      app.logger.log_warning('Reverting to default error template.')
      original_HTTPError_setup_response(self, status, headers, body)
      return

  self.response = response.Response.from_data(status, headers, body)


def register_config(config):
  config.templates = templates_config
  config.hooks.append('template')
  config.postprocessors.append('template')


def register_driver(drivers):
  drivers.register('hook', 'template', TemplateHook)

  drivers.add_interface(
    'template',
    TemplateInterface,
    config=templates_config,
    drivers={
      'jinja2': Jinja2Driver
    }
  )

  errors.HTTPError.setup_response = HTTPError_setup_response

  def init_hook(app):
    current_driver = templates_config.driver
    app.template_engine = drivers.template.load_current(
      loaders=templates_config.loaders,
      globals=templates_config.globals,
      filters=templates_config.filters,
      suffix=templates_config.suffix,
      directory=templates_config.directory,
      extensions=templates_config.extensions
    )

  drivers.register('postprocessor', 'template', templatize)
  drivers.register('init_hook', 'template', init_hook)



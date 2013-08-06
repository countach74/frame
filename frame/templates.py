from driverinterface import DriverInterface
from dotdict import DotDict
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader
from abc import ABCMeta, abstractmethod, abstractproperty
import os


templates_config = DotDict({
  'directory': 'templates',
  'driver': 'jinja2',
  'globals': {},
  'filters': {},
  'jinja2': {
    'loaders': [
      PackageLoader('frame', 'templates')
    ]
  },
  'options': {
    'loaders': []
  },
  'extension': '.html'
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

  @abstractmethod
  def get_global(self, key):
    '''
    Should return global with the given key or return None.
    '''
    pass

  @abstractmethod
  def set_global(self, key, value):
    '''
    Set the global key with value.
    '''
    pass

  @abstractmethod
  def del_global(self, key):
    '''
    Delete a global by key.
    '''
    pass

  @abstractmethod
  def get_filter(self, key):
    '''
    Return filter with given key or return None
    '''
    pass

  @abstractmethod
  def set_filter(self, key, value):
    '''
    Set the filter key with value.
    '''
    pass

  @abstractmethod
  def del_filter(self, key):
    '''
    Delete a filter by key.
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
    loaders.insert(0, FileSystemLoader(templates_config.directory))

    self.environment = Environment(
      loader=ChoiceLoader(loaders))

  def render(self, template, data):
    return self.environment.get_template(template).render(**data)

  def get_template(self, *args, **kwargs):
    return self.environment.get_template(*args, **kwargs)

  def get_global(self, key):
    return self.environment.globals[key]

  def set_global(self, key, value):
    self.environment.globals[key] = value

  def del_global(self, key):
    del(self.environment.globals[key])

  def get_filter(self, key):
    return self.environment.filters[key]

  def set_filter(self, key, value):
    self.environment.filters[key] = value

  def del_filter(self, key):
    del(self.environment.filters[key])

  @property
  def globals(self):
    return self.environment.globals

  @property
  def filters(self):
    return self.environment.filters


class TemplateInterface(DriverInterface):
  def __init__(self, *args, **kwargs):
    import _app
    self.app = _app.app
    DriverInterface.__init__(self, *args, **kwargs)

  def init(self, driver, *args, **kwargs):
    driver_object = driver(*args, **kwargs)

    for k, v in templates_config.globals.iteritems():
      driver_object.set_global(k, v)

    for k, v in templates_config.filters.iteritems():
      driver_object.set_filter(k, v)

    return driver_object

  def get_template(self, *args, **kwargs):
    return self.app.template_engine.get_template(*args, **kwargs)

  def get_global(self):
    return self.app.template_engine.get_global(key)

  def set_global(self, key, value):
    self.app.template_engine.set_global(key, value)

  def del_global(self, key):
    self.app.template_engine.del_global(key)

  def get_filter(self, key):
    return self.app.template_engine.get_filter(key)

  def set_filter(self, key, value):
    self.app.template_engine.set_filter(key, value)

  def del_filter(self, key):
    self.app.template_engine.del_filter(key)

  @property
  def globals(self):
    return self.app.template_engine.globals

  @property
  def filters(self):
    return self.app.template_engine.filters



class TemplateHook(object):
  def __init__(self, app, controller):
    self.app = app
    self.controller = controller

  def __enter__(self):
    self.controller.get_template = self.app.drivers.template.current.get_template

  def __exit__(self, e_type, e_value, e_tb):
    pass


def templatize(request, response):
  if isinstance(response.body, dict):
    class_name = response.action.im_class.__name__
    action_name = response.action.__name__

    template_path = os.path.join(
      class_name.lower(),
      action_name + templates_config.extension
    )   

    try:
      response.body = response.app.template_engine.render(
        template_path, response.body)
    except Exception, e:
      import errors
      raise errors.Error500


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

  drivers.register('postprocessor', 'template', templatize)

  import _app
  current_driver = templates_config.driver
  _app.app.template_engine = drivers.template.load_current(**templates_config.options)

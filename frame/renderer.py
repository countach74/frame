'''
Created on Aug 10, 2013

@author: countach74
'''

from _logger import logger
from _config import config
from errors import Error500, HTTPError
from response import Response
import types
import contextlib


class Renderer(object):
  def __init__(self, app, response, start_response):
    self.app = app
    self.request = app.request
    self.response = response
    self.start_response = start_response
    
  def _render_response(self, response):
    # Apply pre processors, then render the response
    for i in self.app.preprocessors:
      i(self.request, response)
    response.render()
    
    # Need to do something more elegant to handle generators/chunked encoding...
    # Also need to come up with a better way to log chunked encodings
    if type(response.body) is types.GeneratorType:
      self.start_response(response.status, response.headers.items())
      response_length = 0
      for i in response.body:
        yield str(i)
        response_length += len(i)
      logger.log_request(self.request, response, response_length)

    else:
      # Apply post processors
      temp_data = {'response': response}

      def apply_postprocessors():
        for i in self.app.postprocessors:
          new_response = i(self.request, temp_data['response'])
          if new_response and isinstance(new_response, Response):
            temp_data['response'] = new_response
            apply_postprocessors()

      apply_postprocessors()

      response = temp_data['response']
      
      # Deliver the goods
      self.start_response(response.status, response.headers.items())
      yield str(response.body)
      try:
        logger.log_request(self.request, response, len(response.body) if response.body else 0)
      except Exception:
        pass
    
  def render(self):
    response = self.response
    
    if 'match' in self.app.thread_data:
      hooks = map(
        lambda x: self.app.drivers.hook.load_driver(x, self.app,
          response.action.im_self),
        config.hooks)

      try:
        hooks.sort(key=lambda x: x.priority)
      except Exception:
        response = Error500().response

    else:
      hooks = []
      
    def wrap_response(response):
      with contextlib.nested(*hooks):
        for i in self._render_response(response):
          yield i
      self.app.thread_data.clean()
    
    try:
      for i in wrap_response(response):
        yield i
    except HTTPError, e:
      for i in wrap_response(e.response):
        yield i
    except Exception:
      for i in wrap_response(Error500().response):
        yield i
        
  __iter__ = render
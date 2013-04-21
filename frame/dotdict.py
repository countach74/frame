import pprint


class DotDict(dict):
  '''
  A simple subclass of :class:`dict` that allows for dot-notation access of all elements.
  This is used rather extensively through Frame to make it easier to access nested items.
  For example, request header data, response header data, and config directives are allow
  stored using this class.
  '''
  
  def __init__(self, data=None):
    new_data = dict(data) if data else {}
    
    for k, v in new_data.iteritems():
      if isinstance(v, dict):
        new_data[k] = DotDict(v)
    
    dict.__init__(self, new_data)

  def __getattr__(self, key):
    try:
      return self[key]
    except KeyError, e:
      raise AttributeError(e)

  def __setattr__(self, key, value):
    if isinstance(value, dict) and not isinstance(value, DotDict):
      self[key] = DotDict(value)
    else:
      self[key] = value

  def prettify(self):
    pprint.pprint(self)
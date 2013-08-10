class Header(object):
  def __init__(self, key, value):
    self.key = key
    self.value = value
    
  def __str__(self):
    return "%s: %s" % (self.key, self.value)
  
  def __repr__(self):
    return "<Header(%s)>" % str(self)
  
  def __eq__(self, other):
    if isinstance(other, str):
      return self.key == other.key
    else:
      return self is other
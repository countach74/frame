'''
Created on Aug 10, 2013

@author: countach74
'''
from threading import current_thread, RLock


class ThreadData(object):
  def __init__(self):
    self._data = {}
    self._lock = RLock()
    
  def __setitem__(self, key, value):
    self._lock.acquire()
    thread = current_thread()
    if thread not in self._data:
      self._data[thread] = {}
    self._data[thread][key] = value
    self._lock.release()
    
  def __getitem__(self, key):
    thread = current_thread()
    return self._data[thread][key]
  
  def __delitem__(self, key):
    del(self[key])
  
  def __contains__(self, key):
    thread = current_thread()
    return key in self._data[thread]
  
  def update(self, data):
    self._lock.acquire()
    thread = current_thread()
    self._data[thread].update(data)
    self._lock.release()
  
  def clean(self):
    thread = current_thread()
    if thread in self._data:
      del(self._data[thread])
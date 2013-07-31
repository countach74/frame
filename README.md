Frame - A Python Web Framework
==============================

Frame is a simple, flexible web framework. It is designed to be both fast to get started with, yet capable of scaling
up to a large application.

Getting started is as simple as:

    import frame
    
    class Root(frame.Controller):
      def index(self):
        return 'Hello, World!'
      
    frame.routes.connect('/', 'root#index')
      
    if __name__ == '__main__':
      frame.start_http()

For more information, [read the docs](http://python.thirteen8.com/frame).

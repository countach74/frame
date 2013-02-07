import sys
sys.path.append("/home/countach74/git/frame/examples/resources")

from resources import frame
application = frame.app
application.template_dir = '/home/countach74/git/frame/examples/resources/templates'
application.static_dir = '/home/countach74/git/frame/examples/resources/static'

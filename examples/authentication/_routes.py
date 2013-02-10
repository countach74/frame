import frame


# Root controller
frame.routes.connect('/', 'root#index')
frame.routes.connect('/login', 'root#login')

# Admin controller
frame.routes.connect('/admin', 'admin#index')

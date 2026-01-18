class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PREFIX'):
            environ['SCRIPT_NAME'] = environ['HTTP_X_FORWARDED_PREFIX']
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(environ['SCRIPT_NAME']):
                environ['PATH_INFO'] = path_info[len(environ['SCRIPT_NAME']):]
        return self.app(environ, start_response)

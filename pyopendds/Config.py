class Config:
    '''Class for configuring and initializing OpenDDS

    The args attribute of the object will be passed to
    TheParticipantFactoryWithArgs.

    This class is a context manager, so it can be used like so:
    >>> with Config() as cfg:
    ...     cfg.default_rtps(False)
    ...     cfg.opendds_debug_level(10)
    ...     cfg.args.extend([
    ...         '-DCPSChunks', '10',
    ...     ])

    Even if no configuration is desired, Config is still needed to initilaize
    PyOpenDDS and OpenDDS. For this the done method can be called directly:
    >>> Config().done()
    '''

    def __init__(self):
        self.args = []
        self.kw = {}

    def default_rtps(self, value: bool = True):
        '''In OpenDDS the default discovery is InfoRepo and the default
        transport is TCP. In PyOpenDDS the default discovery and transport is
        RTPS. Pass False to this to stop PyOpenDDS from setting up RTPS.
        '''
        self.kw['default_rtps'] = value

    def opendds_debug_level(self, level: int = 0):
        if not (0 <= level <= 10):
            raise ValueError('OpenDDS debug level must be between 0 and 10 !')
        self.args.extend(['-DCPSDebugLevel', str(level)])

    def done(self):
        from _pyopendds import init_opendds_impl
        init_opendds_impl(*self.args, **self.kw)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.done()
            return True
        return False

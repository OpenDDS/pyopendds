'''Manage the initialization of OpenDDS and related functionality.
'''


def init_opendds(*args,
        default_rtps=True,
        opendds_debug_level=0):
    '''Initialize OpenDDS using the TheParticipantFactoryWithArgs macro while
    passing the positional arguments in.

    default_rtps
    In PyOpenDDS the default discovery and transport is RTPS. Pass False
    to this to stop PyOpenDDS from setting up RTPS and let OpenDDS default to
    In OpenDDS the default discovery is InfoRepo and the default transport is
    TCP.

    opendds_debug_level
    Debug logging level in OpenDDS which goes from 0 (off) to 10 (most
    verbose). It is printed to stdout.
    '''

    args = list(args)

    if opendds_debug_level > 0:
        if not (1 <= opendds_debug_level <= 10):
            raise ValueError('OpenDDS debug level must be between 0 and 10!')
        args.extend(['-DCPSDebugLevel', str(opendds_debug_level)])

    from _pyopendds import init_opendds_impl
    init_opendds_impl(*args, default_rtps=default_rtps)

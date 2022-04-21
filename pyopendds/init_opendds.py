"""Manage the initialization of OpenDDS and related functionality.
"""

from typing import Tuple


def opendds_version_str() -> str:
    from _pyopendds import opendds_version_str as vs

    return vs()


def opendds_version_tuple() -> Tuple[int, int, int]:
    from _pyopendds import opendds_version_tuple as vt

    return vt()


def opendds_version_dict() -> dict:
    from _pyopendds import opendds_version_dict as vd

    return vd()


def init_opendds(*args: str, default_rtps=True, opendds_debug_level=0) -> None:
    """Initialize OpenDDS using the TheParticipantFactoryWithArgs macro while
    passing the positional arguments in.

    default_rtps
    In PyOpenDDS the default discovery and transport is RTPS. Pass False
    to this to stop PyOpenDDS from setting up RTPS and let OpenDDS default to
    In OpenDDS the default discovery is InfoRepo and the default transport is
    TCP.

    opendds_debug_level
    Debug logging level in OpenDDS which goes from 0 (off) to 10 (most
    verbose). It is printed to stdout.
    """

    args_list = list(args)

    if opendds_debug_level > 0:
        if not (1 <= opendds_debug_level <= 10):
            raise ValueError("OpenDDS debug level must be between 0 and 10!")
        args_list.extend(["-DCPSDebugLevel", str(opendds_debug_level)])

    from _pyopendds import init_opendds_impl

    init_opendds_impl(*args_list, default_rtps=default_rtps)

import sys
import os
from pathlib import Path
from distutils.core import setup, Extension

ace_root = Path(os.environ.get('ACE_ROOT', '../aces/oci_2.2a/ACE_wrappers')).resolve()
dds_root = Path(os.environ.get('DDS_ROOT', '../master/OpenDDS')).resolve()
messenger = Path.cwd().parent.resolve() / 'messenger'

_pyopendds = Extension(
  name = '_pyopendds',
  sources = ['_pyopendds.cpp'],
  language = 'c++',
  include_dirs = [
    str(ace_root),
    str(ace_root / 'TAO'),
    str(dds_root),
    str(messenger),
  ],
  extra_compile_args = [
    '-pthread', '-pipe'
  ],
  runtime_library_dirs = [
    str(ace_root / 'lib'),
    str(dds_root / 'lib'),
    str(messenger),
  ],
  libraries = [
    'DDS_Messenger_Idl',
    'OpenDDS_Shmem',
    'OpenDDS_Rtps_Udp',
    'OpenDDS_Rtps',
    'OpenDDS_Multicast',
    'OpenDDS_Udp',
    'OpenDDS_Tcp',
    'OpenDDS_InfoRepoDiscovery',
    'OpenDDS_Dcps',
    'TAO_BiDirGIOP',
    'TAO_PI',
    'TAO_CodecFactory',
    'TAO_PortableServer',
    'TAO_AnyTypeCode',
    'TAO',
    'ACE',
    'dl',
    'rt ',
  ],
  define_macros = [
    ('_GNU_SOURCE', None),
    ('__ACE__INLINE__', None),
  ],
)

setup(
  name = 'pyopendds',
  version = '0.1',
  description = 'Python Bindings for OpenDDS',
  py_modules = ['pyopendds'],
  ext_modules = [_pyopendds],
)


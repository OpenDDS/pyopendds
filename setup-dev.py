from setuptools import setup, find_namespace_packages

setup(
    name='pyopendds.dev',
    packages=['pyopendds.dev', 'pyopendds.dev.pyidl', 'pyopendds.dev.itl2py'],
    package_data={
        'pyopendds.dev': [
            'include/pyopendds/*',
        ],
        'pyopendds.dev.itl2py': [
            'templates/*',
        ],
    },
    entry_points={
        'console_scripts': [
            'itl2py=pyopendds.dev.itl2py.__main__:main',
            'pyidl=pyopendds.dev.pyidl.__main__:run',
        ],
    },
    install_requires=[
        'Jinja2',
    ],
)


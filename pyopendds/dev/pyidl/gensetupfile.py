
def gen_setup(target_name: str):
    return f"""
from setuptools import setup

setup(
    name='{target_name}',
    version='0.1',
    packages=['{target_name}'],
    url='',
    license='',
    author='Andrea Ruffino',
    author_email='andrea.ruffino@skyconseil.fr',
    description='Python IDL generated with GenPyIDL.'
)
"""

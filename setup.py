from setuptools import setup, find_packages, Extension
import os
import sys
try:
    from Cython.Build import cythonize
    cython_available = True
except ImportError:
    cython_available = False

def get_version():
    """
    Gets the version number. Pulls it from the source files rather than
    duplicating it.
    """
    fn = os.path.join(os.path.dirname(__file__), 'src', 'quadtree', '__init__.py')
    try:
        lines = open(fn, 'r').readlines()
    except IOError:
        raise RuntimeError("Could not determine version number"
                           "(%s not there)" % (fn))
    version = None
    for l in lines:
        # include the ' =' as __version__ might be a part of __all__
        if l.startswith('__version__ =', ):
            version = eval(l[13:])
            break
    if version is None:
        raise RuntimeError("Could not determine version number: "
                           "'__version__ =' string not found")
    return version

PACKAGES = find_packages('src')
if cython_available:
    EXT_MODULES = [] # cythonize([])
else:
    sys.stderr.write("Cython NOT available, building from .C sources\n")
    EXT_MODULES = [
#        Extension('simplegeom._geom2d', 
#                  ['src/simplegeom/_geom2d.c']),
    ]
SCRIPTS = [] 
REQUIREMENTS = []
DATA_FILES = []

setup(
    name = "quadtree",
    version = get_version(),
    packages = PACKAGES,
    package_dir = {"": "src"},
    author = "Martijn Meijers",
    author_email = "b.m.meijers@tudelft.nl",
    description = "Dynamic Point Region Quadtree (2D) for Python",
    url = "https://github.com/bmmeijers/quadtree",
    license = "MIT license",
    ext_modules = EXT_MODULES,
    data_files = DATA_FILES,
    zip_safe = True,
    scripts = SCRIPTS,
    install_requires = REQUIREMENTS,
    classifiers = [
        "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

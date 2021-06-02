# quadtree

A dynamic 2D PR QuadTree (spatial partitioning tree) for Python.

This spatial data structure allows to store points (you can add and remove them).
It has set semantics (duplicate points will be stored only once in the tree).


## Unit tests

Running tests, after installing
(in the project root, i.e. the folder where setup.py resides):

```
python3 -m unittest discover -s test -p "*.py"
```


## License

MIT License


## Acknowledgements

This is a Python port of C++ code originally written by Jason Dietrich:
https://github.com/jrd730/QuadTree (MIT license).

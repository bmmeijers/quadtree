import quadtree

import unittest

def output_points(pts, fh):
    for pt in pts:
        fh.write("POINT({0[0]} {0[1]})\n".format(pt))

def do_output_quadtree(qt):
    print("OUTPUTTING quadTREE")

    with open("/tmp/stored_pts.wkt", "w") as fh:
        fh.write("wkt\n")
        output_points((pt for pt in qt), fh)


import os.path

class TestQuadTreeRangeSearchBug(unittest.TestCase):
    def setUp(self):
        pts = []
        with open(os.path.join(os.path.dirname(__file__), "fixture_search__pts.wkt")) as fh:
            lines = fh.readlines()
        xmin = float('+inf')
        ymin = float('+inf')
        xmax = float('-inf')
        ymax = float('-inf')
        for line in lines:
            stripped = line.strip().replace("POINT(", "").replace(")", "")
            if stripped.startswith("wkt"):
                continue
            tup = tuple(map(float, stripped.split(" ")))
            pts.append(tup)
            xmin = min(tup[0], xmin)
            ymin = min(tup[1], ymin)
            xmax = max(tup[0], xmax)
            ymax = max(tup[1], ymax)
        qt = quadtree.QuadTree([(xmin, ymin), (xmax, ymax)])
        for pt in pts:
            qt.add(pt)
        # do_output_quadtree(qt)
        self.qt = qt
        self.pts = pts

    def tearDown(self):
        self.qt = None
        self.pts = []

    def test_search(self):
        with open(os.path.join(os.path.dirname(__file__), "fixture_search__rect.wkt")) as fh:
            lines = fh.readlines()
            for line in lines:
                stripped = line.strip().replace("POLYGON((", "").replace("))", "")
                if stripped.startswith("wkt"):
                    continue
                poly = [tuple(map(float, item.split(" "))) for item in stripped.split(", ")]

        # search in the tree
        search = [result for result in self.qt.range_search([poly[0], poly[2]])]

        # brute force search the input
        brute = []
        for pt in self.pts:
            if pt[0] >= poly[0][0] and \
                pt[0] <= poly[2][0] and \
                pt[1] >= poly[0][1] and \
                pt[1] <= poly[2][1]:
                brute.append(pt)
        # the points found by brute force should be the same as by using the
        # range search method
        assert set(search) == set(brute)


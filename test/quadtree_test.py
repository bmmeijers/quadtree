import random
import unittest
import time

from quadtree import QuadTree
from quadtree.quadtree import center_size, point_in_region

class TestCenterSize(unittest.TestCase):
    def test_x(self):
        c, s = center_size([(5.0, 5.0), (7.0, 100.0)])
        assert c == (6.0, 52.5)
        assert s == (128.0, 128.0)


class TestQuadTreeRangeSearch(unittest.TestCase):
    def setUp(self):
        self.extent = extent = 1024
        self.qt = QuadTree([(-extent, -extent), (+extent, +extent)], 64)

    def tearDown(self):
        self.qt = None

    def test_range_search(self):
        """add points with a gap around them and find them with rectangle around"""
        gap = 5
        for x in range(-self.extent+1, self.extent, gap):
            for y in range(-self.extent+1, self.extent, gap):
                self.qt.add( (x, y) )
        # with open("/tmp/qt.wkt", "w") as fh:
        #     print("id;wkt;point_count", file=fh)
        #     for node in self.qt.root.preorder():
        #         if node.leaf:
        #             print(f"{id(node)};{node};{len(node.bucket)}", file=fh)
        region = [(-self.extent, -self.extent), (-self.extent+3, -self.extent+3)]
        self.qt.range_search(region)
        # carry out range search for all inserted points
        # ct = 0
        # t0 = time.time()
        for x in range(-self.extent+1, self.extent, gap):
            for y in range(-self.extent+1, self.extent, gap):
                region = [(x-1, y-1), (x+1, y+1)]
                for pt in self.qt.range_search(region):
                    assert pt == (x, y)
        #             ct += 1
        # duration = time.time() - t0
        # print(duration, "range search")
        # print(duration / ct, "range search / search")
        # print(f"range searched {ct} points")


class TestQuadTree(unittest.TestCase):
    def setUp(self):
        self.qt = QuadTree([(-1.0, -1.0), (1.0, 1.0)], 64)

    def tearDown(self):
        self.qt = None

    def test_basic(self):
        self.qt.add((0.005, 0.007))
        self.assertTrue((0.005, 0.007) in self.qt)
        self.assertFalse((2.5, 2.5) in self.qt)

    def test_adding(self):
        for _ in range(100_000):
            x = random.random()
            y = random.random()
            pt = (x, y)
            self.qt.add(pt)

    def test_adding_skewed_up(self):
        size = 2.0
        start = -1.0
        ct = 100_000
        inc = size / ct
        for t in range(ct):
            x = start + t * inc
            y = start + t * inc
            pt = (x, y)
            self.qt.add(pt)

    def test_adding_skewed_down(self):
        size = 2.0
        x_start = -1.0
        y_start = +1.0
        ct = 100_000
        inc = size / ct
        for t in range(ct):
            x = x_start + t * inc
            y = y_start - t * inc
            pt = (x, y)
            self.qt.add(pt)

    def test_removal(self):
        pts = set()
        for _ in range(100_000):
            x = random.random()
            y = random.random()
            pt = (x, y)
            self.qt.add(pt)
            pts.add(pt)

        for pt in self.qt:
            self.assertTrue(pt in pts)

        for pt in pts:
            self.qt.remove(pt)

        for pt in self.qt:
            assert False # it is an error if we find a point in the tree
        else:
            assert True

    def test_containment(self):
        for _ in range(1_000):
            x = random.random()
            y = random.random()
            pt = (x, y)
            self.qt.add(pt)
        # for test, use internal access to the root node
        for node in self.qt.root.preorder():
            if node.leaf:
                for pt in node.bucket:
                    minXY, maxXY = node.region()
                    self.assertTrue(point_in_region(pt, minXY, maxXY))


if __name__ == '__main__':
    unittest.main(module='quadtree_tests')

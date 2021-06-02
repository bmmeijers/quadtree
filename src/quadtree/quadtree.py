"""A dynamic 2D QuadTree (spatial partitioning tree)

The QuadTree has set semantics (duplicate points will be stored once)
"""

import math
from collections import deque

X = 0
Y = 1

LOWER_LEFT_QUAD = 0
UPPER_LEFT_QUAD = 1
LOWER_RIGHT_QUAD = 2
UPPER_RIGHT_QUAD = 3

NODE_NOT_IN_REGION = 0
NODE_PARTIALLY_IN_REGION = 1
NODE_CONTAINED_BY_REGION = 2


def next_pow2(value):
    """Returns next power of 2 for a number"""
    return float(1 << int(math.ceil(math.log2(value))))


def center_size(region):
    """Obtain center and size for the rectangle *region*,
    used for initializing the root node of the QuadTree

    Makes sure that size is a power of 2 (easy split)
    """
    xymin, xymax = region
    x_min, y_min = xymin[X], xymin[Y]
    x_max, y_max = xymax[X], xymax[Y]
    x_size = x_max - x_min
    y_size = y_max - y_min
    center = (x_min + 0.5 * x_size, y_min + 0.5 * y_size)
    hsize = max(next_pow2(x_size), next_pow2(y_size))
    size = (hsize, hsize)
    return center, size


class QuadTreeNode:
    __slots__ = "child", "center", "size", "bucket", "leaf"

    def __init__(self, center, size):
        self.child = [None] * 4
        self.center = tuple(map(float, center))
        self.size = tuple(map(float, size))
        #
        self.bucket = []
        self.leaf = True

    def __str__(self):
        xmin = self.center[X] - self.size[X]
        ymin = self.center[Y] - self.size[Y]
        xmax = self.center[X] + self.size[X]
        ymax = self.center[Y] + self.size[Y]
        return f"POLYGON(({xmin} {ymin}, {xmax} {ymin}, {xmax} {ymax}, {xmin} {ymax}, {xmin} {ymin}))"

    def region(self):
        xmin = self.center[X] - self.size[X]
        ymin = self.center[Y] - self.size[Y]
        xmax = self.center[X] + self.size[X]
        ymax = self.center[Y] + self.size[Y]
        return [(xmin, ymin), (xmax, ymax)]

    def preorder(self):
        """Pre-order traversal of tree rooted at given node."""
        yield self
        for node in self.child:
            if node is not None:
                for n in node.preorder():
                    yield n

    def quadrant(self, point):
        """Returns the quadrant index of a child node given a point by comparing 
        the coordinates of the point to the center of the current node"""
        # get the quadrant that would contain the vertex
        # in reference to a given start node
        q = 0
        if point[X] >= self.center[X]:
            q += 2
        if point[Y] >= self.center[Y]:
            q += 1
        return q

    def child_center(self, quad):
        """Returns the center point of the child, given the quadrant index of the child"""
        v = list(self.center[:])
        if quad == LOWER_LEFT_QUAD:
            v[X] -= self.size[X] / 2.0
            v[Y] -= self.size[Y] / 2.0
        elif quad == UPPER_LEFT_QUAD:
            v[X] -= self.size[X] / 2.0
            v[Y] += self.size[Y] / 2.0
        elif quad == LOWER_RIGHT_QUAD:
            v[X] += self.size[X] / 2.0
            v[Y] -= self.size[Y] / 2.0
        elif quad == UPPER_RIGHT_QUAD:
            v[X] += self.size[X] / 2.0
            v[Y] += self.size[Y] / 2.0
        return tuple(v)

    def fitting_child_node(self, v):
        """Returns the child node that will contain this vertex,
        if the child node does not exist yet, instantiate it.
        """
        # get the next node that would contain the vertex
        # in reference to a given start node
        quad = self.quadrant(v)
        if self.child[quad]:
            return self.child[quad]
        # node not found, so create it
        else:
            r = (self.size[X] / 2.0, self.size[Y] / 2.0)
            self.child[quad] = QuadTreeNode(self.child_center(quad), r)
            return self.child[quad]

    def add_all_points_to_results(self, results):
        """Adds all points of this node its complete subtree to the results list """
        if self.leaf == True:
            results.extend(self.bucket)
        else:
            for child in self.child:
                if child is not None:
                    child.add_all_points_to_results(results)


class QuadTree:
    def __init__(self, region, bucketSize=16):
        center, size = center_size(region)
        #        print(center)
        #        print(rnge)
        self.root = QuadTreeNode(center, size)
        self.max_bucket_size = bucketSize

    def add(self, v):
        """Add point v to the QuadTree"""
        self._insert(v, self.root)

    def _insert(self, v, node):
        """Insert the point to the correct node in the tree
        making modifications to the node structure if needed
        """
        # vertices are stored only in leaf nodes
        # newly created nodes are leaf nodes by default
        if node.leaf:
            # there is room in this node's bucket
            if len(node.bucket) < self.max_bucket_size:
                if v not in node.bucket:
                    # append point, not yet in the tree
                    node.bucket.append(v)
                else:
                    # duplicate point, already in the tree
                    return
            # bucket is full, so push all vertices to next depth,
            # clear the current node's bucket and make it a stem
            else:
                node.leaf = False
                self._insert(v, node.fitting_child_node(v))
                # copy over the vertices to childs
                for v in node.bucket:
                    self._insert(v, node.fitting_child_node(v))
                node.bucket.clear()
        # current node is a stem node used for navigation
        else:
            self._insert(v, node.fitting_child_node(v))

    def __contains__(self, v):
        """Check whether exact point appears in QuadTree."""
        # walk down the tree
        node = self.root
        while not node.leaf:
            quad = node.quadrant(v)
            if node.child[quad]:
                node = node.child[quad]
            else:
                return False
        # we should be at a leaf node now
        assert node.leaf
        # check if the point v is in the bucket of this leaf
        if v in node.bucket:
            return True
        else:
            return False

    def __iter__(self):
        """Pre-order traversal of points in the tree."""
        for node in self.root.preorder():
            if node.leaf:
                for pt in node.bucket:
                    yield pt

    def remove(self, v):
        """Remove point v from the tree"""
        # navigate to leaf node containing the vertex to be deleted
        # keep track of which nodes are visited to be able to
        # reduce nodes in the tree if possible
        trace = []
        trace.append(self.root)
        top = trace[-1]
        while not top.leaf:
            quad = top.quadrant(v)
            if top.child[quad]:
                trace.append(top.child[quad])
                top = trace[-1]
            else:
                return False
        # we should be at a leaf node now
        assert top.leaf
        # linearly search bucket for target vertex
        if v in top.bucket:
            top.bucket.remove(v)
            self._reduce(trace)
            return True
        else:
            return False

    def _reduce(self, trace):
        """Reduce QuadTreeNodes upwards, if possible
        """
        # once a vertex is removed from a leaf node's bucket
        # check to see if that node its parent
        # can consume it together with all of its sibling nodes
        canReduce = True
        trace.pop()
        while canReduce and trace:
            canReduce = True
            top = trace[-1]
            numKeys = 0
            for i in range(4):
                if top.child[i] and not top.child[i].leaf:
                    canReduce = False
                    return
                elif top.child[i] and top.child[i].leaf:
                    numKeys += len(top.child[i].bucket)
            canReduce &= numKeys <= self.max_bucket_size
            # if the [upto] 4 nodes can fit in 1 node, move the points upwards
            if canReduce:
                for i in range(4):
                    if top.child[i]:
                        top.bucket.extend(top.child[i].bucket)
                        top.child[i] = None
                top.leaf = True
            trace.pop()
        return

    def range_search(self, rect):
        """Perform a range search for points, overlapping the rectangle region rect"""
        minXY, maxXY = rect
        results = []
        nodes = deque([])
        nodes.append(self.root)
        while nodes:
            top = nodes[0]
            if top.leaf:
                status = enclosure_status(top.center, top.size, minXY, maxXY)
                # this node is completely contained within the search region
                if status == NODE_CONTAINED_BY_REGION:
                    # add all elements to results
                    results.extend(top.bucket)

                # this node is partially contained by the region
                elif status == NODE_PARTIALLY_IN_REGION:
                    # search through this leaf node's bucket
                    for v in top.bucket:
                        if point_in_region(v, minXY, maxXY):
                            results.append(v)
                # this node definitely has no points in the region
                elif status == NODE_NOT_IN_REGION:
                    # do nothing
                    pass
            else:
                for child in top.child:
                    if child is not None:
                        # check if this nodes children could have points in the region
                        status = enclosure_status(
                            child.center, child.size, minXY, maxXY
                        )
                        # this node is completely contained by region, add all points within
                        if status == NODE_CONTAINED_BY_REGION:
                            child.add_all_points_to_results(results)
                        # this node might contain points in the region
                        # enter it in the queue
                        elif status == NODE_PARTIALLY_IN_REGION:
                            nodes.append(child)
                        # no points in region, discontinue searching this branch
                        elif status == NODE_NOT_IN_REGION:
                            pass
            nodes.popleft()
        return results


def point_in_region(point, minXY, maxXY):
    """Does the point have an overlap with region defined by minXY and maxXY"""
    if (
        (point[X] >= minXY[X])
        and (point[X] <= maxXY[X])   # equal originally excluded for top/right axis
        and (point[Y] >= minXY[Y])
        and (point[Y] <= maxXY[Y])
    ):
        return True
    else:
        return False


def enclosure_status(center, size, minXY, maxXY):
    """How does the rectangle defined by center and size interact with the 
    rectangle defined by the points minXY and maxXY"""

    node_min = (center[X] - size[X], center[Y] - size[Y])
    node_max = (center[X] + size[X], center[Y] + size[Y])
    # separating axis theorem
    if node_min[X] > maxXY[X] or node_max[X] < minXY[X] or node_min[Y] > maxXY[Y] or node_max[Y] < minXY[Y]:
        # node outside rectangle
        return NODE_NOT_IN_REGION
    else:
        # node can be fully contained or partially overlapping
        # let's figure out by looking at the node its corners
        enclosed_pts = 0
        enclosed_pts += point_in_region(
            (center[X] - size[X], center[Y] - size[Y]), minXY, maxXY
        )
        enclosed_pts += point_in_region(
            (center[X] - size[X], center[Y] + size[Y]), minXY, maxXY
        )
        enclosed_pts += point_in_region(
            (center[X] + size[X], center[Y] - size[Y]), minXY, maxXY
        )
        enclosed_pts += point_in_region(
            (center[X] + size[X], center[Y] + size[Y]), minXY, maxXY
        )
        if enclosed_pts == 4:
            return NODE_CONTAINED_BY_REGION
        else:
            return NODE_PARTIALLY_IN_REGION



def _testX():
    tree = QuadTree([(-512, -512), (512, 512)], 4)
    tree.add((205, 205))
    tree.add((205, 205))

    tree.add((1, 1))
    tree.add((2, 2))
    tree.add((3, 3))

    tree.add((4, 4))

    with open("/tmp/serialization1.wkt", "w") as fh:
        print("wkt;count;is_leaf;points", file=fh)
        for node in tree:
            print(f"{node};{len(node.bucket)};{node.leaf};{node.bucket}", file=fh)

    tree.remove((206, 206))
    tree.remove((510, 510))

    for i in range(1, 5):
        tree.remove((i, i))

    with open("/tmp/serialization2.wkt", "w") as fh:
        print("wkt;count;is_leaf;points", file=fh)
        for node in tree:
            print(f"{node};{len(node.bucket)};{node.leaf};{node.bucket}", file=fh)

    print(tree.size_search([(-2048, -2048), (2048, 2048)]))


def _testY():
    import random

    qt = QuadTree([(-1.0, -1.0), (1.0, 1.0)], 64)
    for _ in range(1_000):
        x = random.random()
        y = random.random()
        pt = (x, y)
        qt.add(pt)
    for node in qt:
        if node.leaf:
            for pt in node.bucket:
                minXY, maxXY = node.region()
                print(pt)
                print(minXY, maxXY)
                assert point_in_region(pt, minXY, maxXY)


if __name__ == "__main__":
    _testX()
    _testY()

# -*- coding: utf-8 -*-
"""
Copyright (C) 2015-2016 Michał Czuczman

This file is part of Did.

Did is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

Did is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Foobar; if not, write to the Free Software Foundation, Inc., 51 Franklin St,
Fifth Floor, Boston, MA  02110-1301  USA
"""

import unittest
import datetime
from report import AggregateTreeNode


class TestNameSimplification(unittest.TestCase):
    def setUp(self):
        self.t1 = datetime.timedelta(0, 10)

    def tearDown(self):
        pass

    def assertTreeEqual(self, got, expected):
        if expected is None:
            self.assertTrue(isinstance(got, datetime.timedelta))
        else:
            self.assertSetEqual(set(got.children.keys()), set(expected.keys()))
            for key in got.children.keys():
                self.assertTreeEqual(got.children[key], expected[key])

    def test_insert_1_1_level_item(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"": None}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": None})

    def test_insert_2_1_level_items(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a"], self.t1, False)
        tree.add_interval(["x"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"": None}, "x": {"": None}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": None, "x": None})

    def test_insert_repeated_1_level_item(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a"], self.t1, False)
        tree.add_interval(["a"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"": None}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": None})

    def test_insert_1_2_level_item(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"": None}}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a b": None})

    def test_insert_2_2_level_items(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b"], self.t1, False)
        tree.add_interval(["x", "y"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"": None}}, "x": {"y": {"": None}}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a b": None, "x y": None})

    def test_insert_2_2_level_items_with_common_level_1(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b"], self.t1, False)
        tree.add_interval(["a", "c"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"": None}, "c": {"": None}}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": {"b": None, "c": None}})

    def test_insert_2_3_level_items_with_common_level_1(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b", "c"], self.t1, False)
        tree.add_interval(["a", "d", "e"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"c": {"": None}}, "d": {"e": {"": None}}}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": {"b c": None, "d e": None}})

    def test_insert_2_3_level_items_with_common_levels_1_and_2(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b", "c"], self.t1, False)
        tree.add_interval(["a", "b", "d"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"c": {"": None}, "d": {"": None}}}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a b": {"c": None, "d": None}})

    def test_insert_2_3_level_items_with_common_level_1_and_1_different_level_1(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b", "c"], self.t1, False)
        tree.add_interval(["a", "d", "e"], self.t1, False)
        tree.add_interval(["x"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"c": {"": None}}, "d": {"e": {"": None}}}, "x": {"": None}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": {"b c": None, "d e": None}, "x": None})

    def test_insert_2_3_level_items_with_common_levels_1_and_2_and_1_different_level_1(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b", "c"], self.t1, False)
        tree.add_interval(["a", "b", "d"], self.t1, False)
        tree.add_interval(["x"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"c": {"": None}, "d": {"": None}}}, "x": {"": None}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a b": {"c": None, "d": None}, "x": None})

    def test_insert_2_3_level_items_with_common_levels_1_and_2_and_1_with_common_level_1(self):
        tree = AggregateTreeNode()
        tree.add_interval(["a", "b", "c"], self.t1, False)
        tree.add_interval(["a", "b", "d"], self.t1, False)
        tree.add_interval(["a", "x"], self.t1, False)
        self.assertTreeEqual(tree, {"a": {"b": {"c": {"": None}, "d": {"": None}}, "x": {"": None}}})
        tree.simplify()
        self.assertTreeEqual(tree, {"a": {"b": {"c": None, "d": None}, "x": None}})


if __name__ == "__main__":
    unittest.main()

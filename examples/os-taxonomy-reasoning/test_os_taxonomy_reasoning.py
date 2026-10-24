import unittest
from os_taxonomy_reasoning import fixture, prerequisite_map, ordered_dependencies, run

class TaxonomyReasoningTests(unittest.TestCase):
    def test_prerequisites_precede_target(self):
        topics, edges, query = fixture()
        result = run(topics, edges, query)
        self.assertEqual([x["id"] for x in result["ordered_plan"]], ["t1", "t2", "t3"])
        self.assertEqual(result["matched_target"], "Add two-digit numbers")

    def test_soft_edges_excluded_by_default(self):
        self.assertEqual(prerequisite_map([{"topicId":"b","prerequisiteId":"a","strength":"soft"}]), {})

    def test_soft_edges_can_be_included(self):
        graph = prerequisite_map([{"topicId":"b","prerequisiteId":"a","strength":"soft"}], True)
        self.assertEqual(len(graph["b"]), 1)

    def test_cycle_is_reported(self):
        graph = {"a":[{"prerequisiteId":"b"}], "b":[{"prerequisiteId":"a"}]}
        with self.assertRaisesRegex(ValueError, "Cycle detected"):
            ordered_dependencies("a", graph)

if __name__ == "__main__":
    unittest.main()

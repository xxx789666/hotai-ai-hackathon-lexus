# -*- coding: utf-8 -*-
"""條目 13 只在官網，檢索進正文時必須改成 2026 手冊條目 52。"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_messages as gen


class HandbookSwapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = gen.load_kb()
        cls.vecs, cls.idf = gen.index_kb(rows)

    def test_website_only_entry_13_is_replaced_by_handbook_52(self):
        hits = gen.retrieve(
            "2024/1/1|69,000|建議售價|自用車或租賃車|免費延保",
            self.vecs,
            self.idf,
            k=5,
        )
        ids = [hit["id"] for hit in hits]
        self.assertNotIn("13", ids)
        self.assertIn("52", ids)
        swapped = next(hit for hit in hits if hit["id"] == "52")
        self.assertNotIn("2024/1/1", swapped["text"])
        self.assertNotIn("69,000", swapped["text"])
        self.assertIn("連續準時 8 次定保", swapped["text"])

    def test_cells_that_rank_13_swap_its_slot_to_52(self):
        queries = {
            "過保精算派 T1": "新車基本保證|120,000|免費延長保證|6 個月|8 次|14 萬|69,000|定保套餐",
            "過保精算派 T2": "每一萬公里|每半年|每六個月|6 個月|8 次|免費延長保證|定保套餐|原廠機油",
        }
        for label, query in queries.items():
            hits = gen.retrieve(query, self.vecs, self.idf, k=5)
            ids = [hit["id"] for hit in hits]
            self.assertNotIn("13", ids, label)
            self.assertIn("52", ids, label)
            self.assertEqual(len(ids), len(set(ids)), label)

    def test_required_13_is_forced_as_52(self):
        hits = gen.retrieve_with_required(
            "新車基本保證|120,000|電瓶保證|輪胎保證|免費延長保證|半年|第 5 年",
            self.vecs,
            self.idf,
            ["13"],
            k=5,
        )
        ids = [hit["id"] for hit in hits]
        self.assertEqual(ids[0], "52")
        self.assertNotIn("13", ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_basic_warranty_retrieval_unchanged(self):
        hits = gen.retrieve("新車基本保證|120,000", self.vecs, self.idf, k=3)
        self.assertEqual(hits[0]["id"], "1")
        self.assertNotIn("13", [hit["id"] for hit in hits])


if __name__ == "__main__":
    unittest.main()

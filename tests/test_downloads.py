"""Hand-established portable names for invented table labels."""

import unittest

from ravel.downloads import table_stem


class DownloadNameTests(unittest.TestCase):
    def test_names_use_the_table_label_with_safe_fallbacks(self):
        for name, expected in [
            ('test_measurements', 'test_measurements'),
            ('Test measurements', 'test_measurements'),
            ('../a\\b:c?*"<>|\n', 'a_b_c'),
            ('  . / 🔬 \u202e ', 'table'),
            ('CON', 'table_con'), ('LPT¹', 'table_lpt1'),
            ('Mäßung α', 'mässung_α'), ('ＡＢＣ', 'abc'),
        ]:
            with self.subTest(name=name):
                self.assertEqual(table_stem(name), expected)
        self.assertEqual(table_stem('a' * 200), 'a' * 80)


if __name__ == '__main__':
    unittest.main()

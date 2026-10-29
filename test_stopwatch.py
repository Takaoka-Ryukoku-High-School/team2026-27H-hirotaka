import unittest

from main import add_history_entry, average_history, format_elapsed


class StopwatchFormatTests(unittest.TestCase):
    def test_format_elapsed_seconds(self):
        self.assertEqual(format_elapsed(3661.5), "01:01:01.50")

    def test_format_elapsed_less_than_minute(self):
        self.assertEqual(format_elapsed(9.7), "00:00:09.70")

    def test_add_history_entry(self):
        history = []
        history = add_history_entry(history, 12.34)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["duration"], "00:00:12.34")
        self.assertIn("timestamp", history[0])

    def test_average_history(self):
        history = [{"elapsed": 10.0}, {"elapsed": 20.0}, {"elapsed": 30.0}]
        self.assertAlmostEqual(average_history(history), 20.0)


if __name__ == "__main__":
    unittest.main()

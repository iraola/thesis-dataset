"""
Unit tests to verify methods for data manipulation in data_prep.py.
"""

import unittest

import pandas as pd

from data_prep import insert_row, fill_to_complete_cycles


class Test(unittest.TestCase):
    def test_insert_row(self):
        # Create a sample DataFrame
        df = pd.DataFrame({'values': range(5)}, index=range(0, 10, 2))

        # Insert a new row at index 2 (third position) with value 100
        df = insert_row(df, 2, [100])

        # Assert index and values
        self.assertEqual(list(df.index), [0, 2, 4, 6, 8, 10])
        self.assertEqual(list(df['values']), [0, 1, 100, 2, 3, 4])

    def test_insert_row_three_column(self):
        # Create a sample DataFrame
        df = pd.DataFrame({'values1': [10, 20, 30, 40, 50],
                           'values2': [1, 2, 3, 4, 5],
                           'values3': [100, 200, 300, 400, 500]},
                          index=range(0, 15, 3))

        # Insert a new row at index 3 (fourth position)
        df = insert_row(df, 3, [-1, -2, -3])

        # Assert index and values
        self.assertEqual(list(df.index), [0, 3, 6, 9, 12, 15])
        self.assertEqual(list(df['values1']), [10, 20, 30, -1, 40, 50])
        self.assertEqual(list(df['values2']), [1, 2, 3, -2, 4, 5])
        self.assertEqual(list(df['values3']), [100, 200, 300, -3, 400,
                                               500])

    def test_fill_to_complete_cycles(self):
        # Build example dataframe
        n_cycle = 4
        sample_time = 2
        df = pd.DataFrame(
            {'values': [0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0]},
            index=range(sample_time, 13 * sample_time, sample_time))
        df = fill_to_complete_cycles(df, n_cycle, sampling_time=sample_time,
                                     ref_col='values')
        # Assertions
        self.assertEqual(len(df), 14)
        self.assertEqual(list(df.index),
                         [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28])
        self.assertEqual(list(df['values']),
                         [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0])

    def test_fill_to_complete_cycles_big(self):
        # Build example dataframe
        n_cycle = 5
        sample_time = 3
        length = 14
        df = pd.DataFrame(
            {'SP(19)': [0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1],
             'values': list(range(101, 101 + length))},
            index=range(sample_time, (length + 1) * sample_time, sample_time))
        df = fill_to_complete_cycles(df, n_cycle, sampling_time=sample_time,
                                     ref_col='SP(19)')
        # Assertions
        self.assertEqual(len(df), length + 3)
        self.assertEqual(
            list(df.index), [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39,
                             42, 45, 48, 51])
        self.assertEqual(
            list(df['SP(19)']),
            [0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1])
        self.assertEqual(
            list(df['values']),
            [101, 102, 103, 104, 105, 106, 107, 108, 108, 108, 109, 110,
             111, 112, 112, 113, 114])

    def test_fill_to_complete_cycles_excess(self):
        """
        Check case where there are more and not fewer instances in cycle.
        """
        # Build example dataframe
        n_cycle = 4
        sample_time = 2
        df = pd.DataFrame(
            {'values': [0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0]},
            index=range(sample_time, 16 * sample_time, sample_time))
        df = fill_to_complete_cycles(df, n_cycle, sampling_time=sample_time,
                                     ref_col='values')
        # Assertions
        self.assertEqual(len(df), 14)
        self.assertEqual(list(df.index),
                         [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28])
        self.assertEqual(list(df['values']),
                         [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0])


if __name__ == '__main__':
    unittest.main()

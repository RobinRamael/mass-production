from unittest import TestCase

import six

from mass_production import Conveyor

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock


def f(**kwargs):
    return kwargs


class ConveyorTests(TestCase):

    def test_using(self):
        kwargs = (Conveyor(f)
                  .using(a=1, b=2)
                  .of_size(5))

        self.assertEqual(kwargs, [{'a': 1, 'b': 2}] * 5)

    def test_permutate(self):
        kwargs = (Conveyor.call(f)
                  .permutating(x=[1, 2, 3], y='abc')
                  .of_size(10))

        # -> Factory.create will be called with the following kwargs:
        expected = [{'x': 1, 'y': 'a'},
                    {'x': 2, 'y': 'a'},
                    {'x': 3, 'y': 'a'},
                    {'x': 1, 'y': 'b'},
                    {'x': 2, 'y': 'b'},
                    {'x': 3, 'y': 'b'},
                    {'x': 1, 'y': 'c'},
                    {'x': 2, 'y': 'c'},
                    {'x': 3, 'y': 'c'},
                    {'x': 1, 'y': 'a'}]  # sequence restarts after 9 iterations

        six.assertCountEqual(self, expected, kwargs)

    def test_of_convertable_float_size(self):
        kwargs = (Conveyor(f)
                  .using(x=1)
                  .of_size(10.0))

        self.assertEqual(kwargs, [{'x': 1}] * 10)

    def test_of_unconvertable_float_size(self):
        with self.assertRaises(ValueError):
            (Conveyor(f)
             .using(x=1)
             .of_size(10.5))

    def test_cycling(self):
        kwargs = (Conveyor(f)
                  .cycling(x=range(2))
                  .of_size(10.0))

        self.assertEqual(kwargs, [{'x': 0}, {'x': 1}] * 5)

    def test_from_table(self):
        kwargs = (Conveyor.call(f)
                  .using(alive=True)
                  .from_table(('age', 'hair_color', 'job'),
                              [(36, 'blond', 'Developer'),
                               (18, 'brown', 'Student'),
                               (5, 'black', None),
                               (72, 'grey', 'Pensioner')]))

        expected = [{'age': 36, 'hair_color': 'blond',
                     'job': 'Developer', 'alive': True},
                    {'age': 18, 'hair_color': 'brown',
                     'job': 'Student', 'alive': True},
                    {'age': 5, 'hair_color': 'black',
                     'job': None, 'alive': True},
                    {'age': 72, 'hair_color': 'grey',
                     'job': 'Pensioner', 'alive': True}]

        self.assertEqual(kwargs, expected)

    def test_for_each(self):
        kwargs = (Conveyor.call(f)
                  .using(name='Alice')
                  .for_each(where=['In Wonderland', 'In Chains']))

        expected = [{'name': 'Alice', 'where': 'In Wonderland'},
                    {'name': 'Alice', 'where': 'In Chains'}]

        self.assertEqual(kwargs, expected)

    def test_override(self):
        kwargs = (Conveyor(f)
                  .using(a=1, b=2)
                  .cycling(a=[True, False])
                  .using(b=3)
                  .of_size(10))

        self.assertEqual(kwargs,
                         [{'a': True, 'b': 3}, {'a': False, 'b': 3}] * 5)

    def test_empty(self):
        kwargs = (Conveyor.call(f)
                  .using()
                  .cycling()
                  .permutating()
                  .for_each(key=[]))

        self.assertEqual(kwargs, [])

    def test_empty_kwarg_seqs(self):
        kwargs = (Conveyor.call(f)
                  .cycling(b=[])
                  .permutating(a=[], c=[])
                  .of_size(3))

        self.assertEqual(kwargs, [{}, {}, {}])

    def test_no_config(self):
        kwargs = Conveyor.call(f).of_size(3)

        self.assertEqual(kwargs, [{}, {}, {}])

    def test_no_function_specified(self):
        with self.assertRaises(ValueError):
            (Conveyor(None).of_size(2))

    def test_no_callable_specified(self):
        with self.assertRaises(ValueError):
            (Conveyor('This is not a callable').of_size(2))

    def test_empty_for_each(self):
        with self.assertRaises(ValueError):
            (Conveyor(f).for_each())

    def test_for_each_lenghts_not_equal(self):
        with self.assertRaises(ValueError):
            (Conveyor(f).for_each(x=[1, 2], y=[1, 2, 3]))

    def test_table_header_length_doesnt_match_rows(self):
        with self.assertRaises(ValueError):
            (Conveyor(f).from_table(
                ['one', 'two'],
                [[1, 2, 3],
                 [1, 2, 3],
                 [1, 2, 3]]))

    def test_table_rows_not_all_same_lenghts(self):
        with self.assertRaises(ValueError):
            (Conveyor(f).from_table(
                ['one', 'two', 'three'],
                [[1, 2, 3],
                 [1, 2, 3],
                 [1, 2, 3, 4]]))

    def test_create_batch_from_called(self):
        # We don't need an actual factory to test if the create is called.
        mock_factory = MagicMock()
        (Conveyor.create_batch_from(mock_factory).using(x=1).of_size(1))

        mock_factory.create.assert_called_once_with(x=1)

from collections import OrderedDict
from functools import reduce
from itertools import cycle, islice, product, repeat


def merged(*ds):
    """Merge all given dictionaries"""
    if len(ds) == 2:
        d1, d2 = ds
        d = d1.copy()
        d.update(d2)
        return d
    elif len(ds) == 1:
        return ds[0]

    return reduce(merged, ds, {})


class Conveyor(object):
    """
    This class can be used to call a function (for example a factory-boy
    Factory's `create`) multiple times using a series sets of of kwargs that
    are generated according to the rules specified using the Conveyor's
    self-returning methods:

    Example:
        (Conveyor.call(lambda **kwargs: print(kwargs))
        .using(a=1, b=2)
        .cycling(fruit=['apple', 'banana'], color=['red', 'yellow'],
                 index=itertools.count(1))
        .of_size(5))

        # outputs (when of_size(5) is called)
        {'a': 1, 'b': 2, 'fruit': 'apple', 'color': 'red', 'index': 1}
        {'a': 1, 'b': 2, 'fruit': 'banana', 'color': 'yellow', 'index': 2}
        {'a': 1, 'b': 2, 'fruit': 'apple', 'color': 'red', 'index': 3}
        {'a': 1, 'b': 2, 'fruit': 'banana', 'color': 'yellow', 'index': 4}
        {'a': 1, 'b': 2, 'fruit': 'apple', 'color': 'red', 'index': 5}

    """
    def __init__(self, func):
        self._generators = []
        self.func = func

    @classmethod
    def call(cls, func):
        """
        Set up builder to call the given function.
        """
        return cls(func)

    @classmethod
    def create_batch_from(cls, factory_class):
        """
        Set up builder to call the passed factory's create method.
        """
        return cls.call(factory_class.create)

    def using(self, **kwargs):
        """
        Set up the builder to use the given kwargs for every call. Returns self
        to make calls chainable.
        """
        self._generators.append(repeat(kwargs))
        return self

    def cycling(self, **kwargs_seqs):
        """
        Set up the builder to cycle through the generators and/or lists passed
        for every function call. Returns self to make calls chainable.

        Example:
            (Conveyor.create_batch_from(Factory)
            .cycling(x=[1, 2, 3], y='ab')
            .of_size(10))

            # -> Factory.create will be called with the following kwargs:

            [{'x': 1, 'y': 'a'},
             {'x': 2, 'y': 'b'},
             {'x': 3, 'y': 'a'},
             {'x': 1, 'y': 'b'},
             {'x': 2, 'y': 'a'},
             {'x': 3, 'y': 'b'},
             {'x': 1, 'y': 'a'}]  # sequence restarts after 6 iterations!
        """
        # All kwargs should be in theshape key->generator (or a list)

        # We take each kwarg and make a cycler out of it, a generator that
        # yields single-element dictinaries from the original generator like:
        # {key: value1}, {key: value2}, etc, going back to the beginning if a
        # finite generator stops.

        # we need to build the cycler with a helper function because
        # of how python does its scoping (otherwise only the last k would be
        # added)
        def cycler(k, vals):
            return cycle({k: v} for v in vals)

        # we generate a cycler for each of the keyword arguments:
        gens = []
        for k, vals in kwargs_seqs.items():
            gens.append(cycler(k, vals))

        # we now have n = len(kwargs_seqs) infinite generators, each
        # representing the pattern one kwarg should follow.
        # we now build a kwarg generator where every next element is
        # generated by taking the next element of each of the
        # cyclers we generated and merging all those elements.
        self._generators.append(merged(*kwargs) for kwargs in zip(*gens))

        return self

    def permutating(self, **bases):
        """
        Set up the Conveyor to cycle through the product of the given
        iterators/lists passed as kwargs.  Returns self to make calls
        chainable.

        Example:
            (Conveyor.create_batch_from(Factory)
            .permutating(x=[1, 2, 3], y='abc')
            .of_size(10))

            # -> Factory.create will be called with the following kwargs:

            [{'x': 1, 'y': 'a'},
             {'x': 2, 'y': 'a'},
             {'x': 3, 'y': 'a'},
             {'x': 1, 'y': 'b'},
             {'x': 2, 'y': 'b'},
             {'x': 3, 'y': 'b'},
             {'x': 1, 'y': 'c'},
             {'x': 2, 'y': 'c'},
             {'x': 3, 'y': 'c'},
             {'x': 1, 'y': 'a'}]  # sequence restarts after 3*3 iterations!

        Note:
            We use `itertools.product` to generate these permutations, which
            means that the order that `product` generates is the one that is
            generated by the iterator added to this instance by this method.

            As the ordering of kwargs is not guaranteed in python<3.6, we sort
            the kwargs to be able to guarantee that ordering doesn't change
            when called with the same arguments, but no such guarantee can be
            made when the keyword parameters are changed (so the order of
            permutations might change when some keywords are changed.)
        """
        bases = OrderedDict(sorted(bases.items()))  # see note in docstring

        def permutator():
            for vals in product(*bases.values()):
                yield dict(zip(bases.keys(), vals))

        self._generators.append(cycle(permutator()))
        return self

    def generate_kwargs(self):
        """
        Return a generator that returns the kwargs the function should be
        called with as a dict.
        """
        # now that the Conveyor has been ste up, we are asked to generate the
        # kwargs for the next function call. Again, we take the next element
        # for each of the generators we added to in the setup methods (cycle,
        # permutate, using) (Note that this time, the dicts might be larger
        # than 1 element) and merge those into a single kwarg dict. This can
        # now be used to call the function.

        for kwarg_dicts in zip(*self._generators):
            yield merged(*kwarg_dicts)

    def of_size(self, n):
        """
        Call the function specified earlier in the chain with the given kwargs
        n times.
        """
        if not self.func or not callable(self.func):
            raise ValueError(
                "Could not batch call because no callable was "
                "specified.  Either pass it to the intializer or "
                "use Conveyor.create_batch_from or Conveyor.call.")

        if type(n) == float:
            if int(n) == n:
                n = int(n)
            else:
                raise ValueError("Can only use natural numbers for amounts.")

        # we want n calls, so we take n kwarg dicts from the kwarg generator
        # and call the function with them.
        ret_vals = []
        for kwargs in islice(self.generate_kwargs(), 0, n):
            ret_vals.append(self.func(**kwargs))

        # this is necessary for stuff like
        # Conveyor.call(f).of_size(3) to work as expected, but you
        # shouldn't be doing that.
        if not ret_vals:
            return [self.func() for _ in range(n)]

        return ret_vals

    def for_each(self, **kwargs_seqs):
        """
        Call the function specified earlier in the chain with the given kwargs
        for every element in the kwargs passed here (kwargs must have lengths
        here.)

        Example:
            (Conveyor.create_batch_from(Factory)
            .using(name='Alice')
            .for_each(where=['In Wonderland', 'In Chains']))

            # -> Factory.create will be called with the following kwargs:

            [{'name': 'Alice', 'where': 'In Wonderland'},
             {'name': 'Alice', 'where': 'In Chains'},]
        """
        if not kwargs_seqs:
            raise ValueError("Conveyor.for_each takes at least one kwarg "
                             "sequence as argument")

        kwargs_seqs = dict(**kwargs_seqs)
        lengths = [len(seq) for kw, seq in kwargs_seqs.items()]

        if not len(set(lengths)) == 1:
            raise ValueError("kwargs passed to for_each must all be "
                             "the same length")

        return self.cycling(**kwargs_seqs).of_size(lengths[0])

    def from_table(self, header, rows):
        """
        Call the function specified earlier in the chain with the kwargs
        specified by the header and values specified by the rows.

        Example:
        (Conveyor.create_batch_from(PersonFactory)
         .using(alive=True)
         .from_table(('age', 'hair_color', 'job'),
                     [(36, 'blond', 'Developer'),
                      (18, 'brown', 'Student'),
                      (5, 'black', None),
                      (72, 'grey', 'Pensioner'),])

            # -> Factory.create will be called with the following kwargs:

            {'age': 36, 'hair_color': 'blond',
             'job': 'Developer', 'alive': True},
            {'age': 18, 'hair_color': 'brown',
             'job': 'Student', 'alive': True},
            {'age': 5, 'hair_color': 'black',
             'job': None, 'alive': True},
            {'age': 72, 'hair_color': 'grey',
             'job': 'Pensioner', 'alive': True},)
        """
        value_lengths = set(len(row) for row in rows)
        if not len(value_lengths) == 1:
            raise ValueError("All rows should have the same length!")

        if value_lengths != set([len(header)]):
            raise ValueError("Header and value rows are not of same length.")

        kwargs = {}
        for i, col in enumerate(header):
            kwargs[col] = [row[i] for row in rows]

        return self.for_each(**kwargs)

# Mass Production with Conveyor

The Conveyor class enables calling a single function a specified number of
times with keyword arguments that change according to a pattern specified by
chaining method calls.


## Example

This library was orginally developed for use with factory-boy factories:

```python
class Person(object):
    def __init__(self, name=None, hair_color=None, job=None, age=None):
        self.name = name
        self.hair_color = hair_color
        self.job = job
        self.age = age

    def __repr__(self):
        return ('Person(name={}, hair_color={}, job={}, age={})'
                .format(self.name, self.hair_color, self.job, self.age))


from factory import Factory

class PersonFactory(Factory):
    class Meta:
        model = Person

    name = 'Jane Doe'
    hair_color = 'blond'
    job = 'Developer'
    age = 25


from mass_production import Conveyor

people = (Conveyor.create_batch_from(PersonFactory)
          .cycling(job=['Developer', 'Designer'],
                   hair_color=['blond', 'black', 'brown'])
          .from_table(['name', 'age'],
                      [['Eva', 25],
                       ['Arno', 28],
                       ['Margaux', 31],
                       ['George', 46],
                       ['Mary', 52],
                       ['Sander', 22]]))

# returns:
[Person(name='Eva', hair_color='blond', job='Developer', age=25),
 Person(name='Arno', hair_color='black', job='Designer', age=28),
 Person(name='Margaux', hair_color='brown', job='Developer', age=31),
 Person(name='George', hair_color='blond', job='Designer', age=46),
 Person(name='Mary', hair_color='black', job='Developer', age=52),
 Person(name='Sander', hair_color='brown', job='Designer', age=22)]

 ```

You don't have to use factory-boy though, you can specify any function using
`Converyor.call`: The above is equivalent when `Conveyor.call(PersonFactory.create)` is used instead of `Conveyor.create_batch_from(PersonFactory)`


## Notice

Look. This utility was developed to make repeating code a little easier
to read by avoiding huge blocks of almost-repeating statements.
Using it is a balancing act, though, it's very easy to change a
slightly unreadable block of code into a completely unreadable Conveyor
statement. Think. Do I need to use Conveyor or is it readable without it?
Does a single for loop suffice?


## Installation

    pip install mass-production

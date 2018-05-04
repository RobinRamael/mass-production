from setuptools import setup

setup(name='mass-production',
      version='1.0.2',
      description="Call a function (e.g a factory-boy Factory's create method) "
                  "according to a defined pattern.",
      url='http://github.com/RobinRamael/mass-production',
      author='Robin Ramael',
      author_email='robin.ramael@gmail.com',
      license='MIT',
      packages=['mass_production'],
      test_suite='nose.collector',
      tests_require=['nose'],
      include_package_data=True,
      zip_safe=False)

from setuptools import setup, find_packages

version = 0.1

requires = ['bulbs >=0.3.13',
            'PyYAML >=3.09',
            ]


setup(name='neoacl',
      version=version,
      description='An ACL manager using neo4j as backend',
      classifiers=["Programming Language :: Python"],
      author='Aymeric Barantal',
      author_email='mric@chamal.fr',
      url='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="",
      entry_points="""\
[console_scripts]
""",
      )

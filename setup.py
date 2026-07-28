from setuptools import setup, find_packages
setup(
    name='oriel-language',
    version='0.3.0',
    description='ORIEL 0.3 language foundation',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires='>=3.10',
    entry_points={'console_scripts':['oriel=oriel.cli:main']},
)

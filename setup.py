from setuptools import setup, find_packages

setup(
    name="zero_day_ml",
    version="0.0.0",
    packages=find_packages(where="ml/src"),
    package_dir={"": "ml/src"},
)

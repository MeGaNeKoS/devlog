from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    README = f.read()

setup(
    name='python-devlog',
    version='1.1',
    description="No more logging in your code business logic with decorators",
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/MeGaNeKoS/devlog',
    license='MIT',
    author='めがねこ',
    author_email='evictory91@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(),
    keywords=['clean code', 'decorators', 'logging'],
)
import os
from setuptools import setup, find_packages

repo_base_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(repo_base_dir, 'README.rst'), 'r') as README:
    long_description = README.read()

if __name__ == '__main__':
    setup(
        name="rpconnect",
        version="0.9.0",
        description="lightweight rpc framework",
        long_description=long_description.strip(),
        author="Eileen Kuehn, Max Fischer",
        author_email='maxfischer2781@gmail.com',
        url='https://github.com/MaineKuehn/rpconnect',
        packages=find_packages(),
        # dependencies
        install_requires=[],
        # metadata for package search
        license='MIT',
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: MIT License',
            'Intended Audience :: Education',
            'Topic :: Education',
            'Programming Language :: Python :: 3 :: Only',
        ],
        keywords='rpc remote-call',
        # unit tests
        test_suite='gksol.gksol_unittests',
    )

from setuptools import setup, find_packages

setup(
    name='labdataforester',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'neo4j',
        'pandas',
        'networkx',
        'tqdm',
        'Pillow', 
        'neomodel' 
    ],
    entry_points={
        'console_scripts': [
            # Add command-line scripts here if needed
        ],
    },
    author='Adam Patch',
    author_email='patch@mit.edu',
    description='A tool for managing and surveying lab metadata using its file tree structure.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ki-preclinical-imaging-and-testing/labdataranger',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

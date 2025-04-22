from setuptools import setup

# Read dependencies from requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='aicommit-cli',
    version='0.1.0', # Start with an initial version
    py_modules=['aicommit'], # Specify the module name (without .py)
    install_requires=required,
    entry_points={
        'console_scripts': [
            'aicommit = aicommit:main', # Map the command 'aicommit' to the main function in aicommit.py
        ],
    },
    author='João Pedro Leopoldino', # Optional: Add your name
    author_email='leopoldinodev@gmail.com', # Optional: Add your email
    description='A CLI tool to generate commit messages using AI', # Optional: Add a description
    long_description=open('README.md').read() if open('README.md') else '', # Optional: Add a README
    long_description_content_type='text/markdown', # Optional
    url='https://github.com/JPLeopoldino/aicommit-cli', # Optional: Add your project URL
    classifiers=[ # Optional: Classifiers help users find your project
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Choose an appropriate license
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: Utilities',
    ],
    python_requires='>=3.6', # Specify the minimum Python version
)

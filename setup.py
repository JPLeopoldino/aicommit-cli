from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='aicommit-cli',
    version='0.1.0',
    py_modules=['aicommit'],
    install_requires=required,
    entry_points={
        'console_scripts': [
            'aicommit = aicommit:main',
        ],
    },
    author='João Pedro Leopoldino',
    author_email='leopoldinodev@gmail.com',
    description='A CLI tool to generate commit messages using AI',
    long_description=open('README.md').read() if open('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/JPLeopoldino/aicommit-cli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: Utilities',
    ],
    python_requires='>=3.6',
)

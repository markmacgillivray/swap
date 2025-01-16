from setuptools import setup, find_packages

setup(
    name = 'swap',
    version = '2.0.0',
    packages = find_packages(),
    install_requires = [
        "Flask",
        "Flask-Login",
        "Flask-WTF",
        "requests"
    ],
    url = 'https://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'A web API layer over an ES backend, with various useful plugins',
    license = 'Copyheart',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Copyheart',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)

from setuptools import setup

setup(
    name='ngram-keylogger',
    version='0.0.1',
    url='https://github.com/t184256/ngram-keylogger',
    author='Alexander Sosedkin',
    author_email='monk@unboiled.info',
    description="ngram-keylogger: typing stats that don't leak passwords",
    py_modules=['ngram_keylogger'],
    install_requires=['Click', 'evdev'],
    entry_points={
        'console_scripts': [
            'ngram-keylogger = ngram_keylogger:cli',
        ],
    },
)

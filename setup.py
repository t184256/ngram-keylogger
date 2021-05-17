from setuptools import setup

setup(
    name='ngram-keylogger',
    version='0.0.1',
    url='https://github.com/t184256/ngram-keylogger',
    author='Alexander Sosedkin',
    author_email='monk@unboiled.info',
    description="ngram-keylogger: typing stats that don't leak passwords",
    packages=[
        'ngram_keylogger',
        'ngram_keylogger.aspect',
        'ngram_keylogger.filter',
        'ngram_keylogger.util',
    ],
    install_requires=['Click', 'evdev', 'pyxdg', 'psutil', 'i3ipc'],
    entry_points={
        'console_scripts': [
            'ngram-keylogger = ngram_keylogger.app:cli',
        ],
    },
)

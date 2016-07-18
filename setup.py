from setuptools import setup

setup(
    name="dslink-python-hue",
    version="0.2.0",
    description="DSLink for Philips Hue",
    url="http://github.com/IOT-DSA/dslink-python-hue",
    author="Dennis Khvostionov",
    author_email="dennisk@dglogik.com",
    license="Apache 2.0",
    install_requires=[
        "dslink == 0.6.16",
        "phue"
    ]
)

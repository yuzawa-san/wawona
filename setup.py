from setuptools import setup
import os

VERSION = "0.0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="wawona",
    description="Easily make office reservations in sequoia from the command line.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="James Yuzawa",
    url="https://github.com/yuzawa-san/wawona",
    project_urls={
        "Issues": "https://github.com/yuzawa-san/wawona/issues",
        "CI": "https://github.com/yuzawa-san/wawona/actions",
        "Changelog": "https://github.com/yuzawa-san/wawona/releases",
    },
    license="MIT License",
    version=VERSION,
    packages=["wawona"],
    entry_points="""
        [console_scripts]
        wawona=wawona.wawona:run
    """,
    install_requires=[
        "requests>=2.31.0",
        "inquirer>=3.2.4",
        "texttable>=1.7.0",
        "keyring>=24.3.1"
    ],
    python_requires=">=3.7",
)
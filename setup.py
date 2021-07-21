import setuptools
import datetime

try:
    from openet_client import __version__ as version, __author__ as author
except ImportError:
    version = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    author = "nickrsan"

if __name__ == "__main__":
    setuptools.setup(
        name="OpenET Client",
        version=version,
        packages=setuptools.find_packages(exclude=("tests",)),
        description=None,
        long_description="",
        license="MIT",
        author=author,
        author_email="nsantos5@ucmerced.edu",
        url='https://github.com/water3d/openet/',
        install_requires=["requests"],
        include_package_data=True,
    )
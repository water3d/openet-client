import setuptools
import datetime

try:
    from openet_client import __version__ as version, __author__ as author
except ImportError:
    version = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    author = "nickrsan"

if __name__ == "__main__":
    setuptools.setup(
        name="openet_client",
        version=version,
        packages=setuptools.find_packages(exclude=("tests",)),
        description="Client for the OpenET web API with useful wrappers to support common workflows and needs with the API",
        long_description="See README at https://github.com/water3d/openet/ for more details. Make sure to install package extras (e.g. pip install 'openet-client[spatial]') for spatial data support in the geodatabase API. It depends on Geopandas, which depends on fiona - this can be challenging to get set up correctly, so it's worth checking the documentation for those projects to install on your system, or use a conda environment and install the conda geopandas package.",
        license="MIT",
        author=author,
        author_email="nsantos5@ucmerced.edu",
        url='https://github.com/water3d/openet/',
        install_requires=["requests"],
        extras_requires={"spatial": ["geopandas"]},
        include_package_data=True,
    )
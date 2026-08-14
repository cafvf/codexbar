from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as distribution_version

try:
    __version__ = distribution_version("codexbar")
except PackageNotFoundError:
    # Direct source-tree imports outside an installed/editable environment are
    # intentionally not a release-version authority.
    __version__ = "0+unknown"

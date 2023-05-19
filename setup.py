from distutils.core import setup
from pathlib import Path


def read_version():
    root = Path(__file__).parent.resolve()
    with open(root / "VERSION", "r") as fp:
        version = fp.read()
        return version
	

setup(
	version	     = read_version(),
	name		 = "localsaga",
	description  = "Simple Python implementation for the Saga distributed transaction pattern",
	author	     = "Balint Nagy",
	author_email = "b.nagy.balint@gmail.com",
	url		     = "https://github.com/bnagybalint/localsaga",
	packages	 = ["localsaga"],
)

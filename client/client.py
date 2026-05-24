"""
Package entry client.client

This module provides the terminal client. It is the same code as the
top-level `cli.py` but placed inside the `client` package so it can be
invoked with `python -m client.client` as requested by the Stage 2
instructions.
"""

from . import _impl as impl


def main():
    impl.main()


if __name__ == '__main__':
    main()

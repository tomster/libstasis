#from pprint import pformat
from stasis.core import Site
import argparse
import logging
import os
import sys


log = logging.getLogger('Stasis')


def excepthook(type, value, tb):
    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a tty-like
        # device, so we call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        import pdb
        import traceback
        # we are NOT in interactive mode, print the exception...
        traceback.print_exception(type, value, tb)
        print
        # ...then start the debugger in post-mortem mode.
        pdb.pm()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path',
        nargs='?')
    parser.add_argument(
        '-v',
        '--verbose',
        action='count')
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level='DEBUG')
    else:
        if args.verbose is None:
            logging.basicConfig(level='ERROR')
        elif args.verbose == 1:
            logging.basicConfig(level='INFO')
        else:
            logging.basicConfig(level='DEBUG')
    if args.debug:
        sys.excepthook = excepthook
    if args.path is None:
        site = Site(os.getcwd())
    else:
        site = Site(os.path.abspath(args.path))
    site.build()

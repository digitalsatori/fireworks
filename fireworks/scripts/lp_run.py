#!/usr/bin/env python

"""
A runnable script for managing a FireWorks database (a command-line interface to launchpad.py)
"""
from argparse import ArgumentParser
import os
import traceback
import yaml
from fireworks.core.fw_config import FWConfig
from fireworks.core.launchpad import LaunchPad
from fireworks.core.firework import FireWork
import ast
import json
from fireworks.core.workflow import Workflow
from fireworks import __version__ as FW_VERSION
from fireworks.utilities.fw_serializers import DATETIME_HANDLER, _get_obj_dict_from_file

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


def add(lp, filename):
    try:
        if '.tar' in filename:
            fwf = Workflow.from_tarfile(filename)
        else:
            obj_dict = _get_obj_dict_from_file(filename)
            if 'fws' in obj_dict:
                fwf = Workflow.from_file(filename)
            else:
                fwf = FireWork.from_file(filename)
        lp.add_wf(fwf)
    except:
        print 'Error reading FireWork/Workflow file.'
        traceback.print_exc()


def lpad():
    m_description = 'This script is used for creating and managing a FireWorks database (LaunchPad). For a list of ' \
                    'available commands, type "lpad -h". For more help on a specific command, ' \
                    'type "lpad <command> -h".'

    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')

    reset_parser = subparsers.add_parser('reset', help='reset a FireWorks database')
    reset_parser.add_argument('password', help="Today's date, e.g. 2012-02-25. Required to prevent \
    against accidental initializations.")

    addwf_parser = subparsers.add_parser('add', help='insert a Workflow from file')
    addwf_parser.add_argument('wf_file', help="path to a FireWork or Workflow file")

    adddir_parser = subparsers.add_parser('add_dir', help='insert all FWs/Workflows in a directory')
    adddir_parser.add_argument('wf_dir', help="path to a directory containing only FireWorks or Workflow files")

    get_fw_parser = subparsers.add_parser('get_fw', help='get a FireWork by id')
    get_fw_parser.add_argument('fw_id', help="FireWork id", type=int)
    get_fw_parser.add_argument('-f', '--filename', help='output filename', default=None)

    get_fw_ids_parser = subparsers.add_parser('get_fw_ids', help='get FireWork ids by query')
    get_fw_ids_parser.add_argument('-q', '--query', help='query (as pymongo string, enclose in single-quotes)',
                                   default=None)

    reservation_parser = subparsers.add_parser('detect_unreserved', help='Find launches with stale reservations')
    reservation_parser.add_argument('--time', help='expiration time (seconds)', default=FWConfig().RESERVATION_EXPIRATION_SECS, type=int)
    reservation_parser.add_argument('--fix', help='cancel bad reservations', action='store_true')

    fizzled_parser = subparsers.add_parser('detect_fizzled', help='Find launches that have FIZZLED')
    fizzled_parser.add_argument('--time', help='expiration time (seconds)', default=FWConfig().RUN_EXPIRATION_SECS, type=int)
    fizzled_parser.add_argument('--fix', help='mark fizzled', action='store_true')

    version_parser = subparsers.add_parser('version', help='Print the version of FireWorks installed')

    parser.add_argument('-l', '--launchpad_file', help='path to LaunchPad file containing central DB connection info',
                        default=FWConfig().LAUNCHPAD_LOC)
    parser.add_argument('-c', '--config_dir', help='path to a directory containing the LaunchPad file (used if -l unspecified)',
                        default=FWConfig().CONFIG_FILE_DIR)
    parser.add_argument('--logdir', help='path to a directory for logging', default=None)
    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('--silencer', help='shortcut to mute log messages', action='store_true')

    args = parser.parse_args()

    if args.command == 'version':
        print FW_VERSION

    else:
        if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, 'my_launchpad.yaml')):
            args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')

        if args.launchpad_file:
            lp = LaunchPad.from_file(args.launchpad_file)
        else:
            args.loglvl = 'CRITICAL' if args.silencer else args.loglvl
            lp = LaunchPad(logdir=args.logdir, strm_lvl=args.loglvl)

        if args.command == 'reset':
            lp.reset(args.password)

        elif args.command == 'detect_fizzled':
            # TODO: report when fixed
            print lp.detect_fizzled(args.time, args.fix)

        elif args.command == 'detect_unreserved':
            # TODO: report when fixed
            print lp.detect_unreserved(args.time, args.fix)

        elif args.command == 'add':
            add(lp, args.wf_file)

        elif args.command == 'add_dir':
            for filename in os.listdir(args.wf_dir):
                add(lp, filename)

        elif args.command == 'get_fw':
            fw = lp.get_fw_by_id(args.fw_id)
            fw_dict = fw.to_dict()
            if args.filename:
                fw.to_file(args.filename)
            else:
                print json.dumps(fw_dict, default=DATETIME_HANDLER, indent=4)

        elif args.command == 'get_fw_ids':
            if args.query:
                args.query = ast.literal_eval(args.query)
            print lp.get_fw_ids(args.query)

if __name__ == '__main__':
    lpad()
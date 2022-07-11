#!/bin/python3

import common as cm

parser = cm.ChecksumsArguments(prog='checksums-verify')
speed = parser.add_mutually_exclusive_group()
speed.add_argument('--only-modified', dest='only_modified', action='store_true',
    help='skip unmodified files')
args = parser.parse_args()
dirs = cm.idirs(args.path, include_hidden=args.include_hidden) if args.recursive else (args.path,)
name = f'{args.prefix}.{args.algorithm}'

for d in dirs:
    sf = d / name
    data = {}

    try:
        if sf.is_file():
            data = cm.read_file(sf)
    except OSError as e:
        cm.print_error(e, e.filename)
        continue

    for df in cm.ifiles(d, include_hidden=args.include_hidden):
        if df not in data:
            cm.print_message('NEW', df)
            continue

        if args.only_modified and cm.is_older(df, data[df]['created']):
            continue # log

        try:
            if data[df]['checksum'] != cm.create_checksum(df, args.algorithm):
                cm.print_message('BAD', df)
            elif args.verbose:
                cm.print_message('OK', df)
        except OSError as e:
            cm.print_error(e, e.filename)
            
#!/bin/python3

import common as cm
from datetime import datetime as dt

parser = cm.ChecksumsArguments(prog='checksums-create')
reset = parser.add_mutually_exclusive_group()
reset.add_argument('--reset-all', dest='reset_all', action='store_true',
    help='resets all checksums')
reset.add_argument('--reset-modified', dest='reset_modified',
    action='store_true', help='resets checksums for modified files')

args = parser.parse_args()
dirs = cm.idirs(args.path, include_hidden=args.include_hidden) if args.recursive else (args.path,)
name = f'{args.prefix}.{args.algorithm}'

for d in dirs:
    sf = d / name
    data = {}
    write = False

    try:
        if sf.is_file() and not args.reset_all:
            data = cm.read_file(sf)
    except OSError as e:
        cm.print_error(e, e.filename)
        continue

    for df in cm.ifiles(d, include_hidden=args.include_hidden):
        if df in data and (not args.reset_modified or
                cm.is_older(df, data[df]['created'])):
            continue

        try:
            data[df] = {}
            data[df]['checksum'] = cm.create_checksum(df, args.algorithm)
        except OSError as e:
            cm.print_error(e, e.filename)
            continue
        else:
            data[df]['created'] = dt.utcnow().isoformat()
            cm.print_message(args.algorithm, df)
            write = True
    try:
        if write and data:
            cm.write_file(sf, data)
    except OSError as e:
        cm.print_error(e, e.filename)

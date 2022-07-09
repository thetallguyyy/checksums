import common as cm

parser = cm.ChecksumsArguments(prog='checksums-verify')
args = parser.parse_args()
dirs = cm.idirs(args.path, include_hidden=args.include_hidden) if args.recursive else (args.path,)
name = f'{args.prefix}.{args.algorithm}'

for d in dirs:
    sf = d / name
    data = {}

    try:
        if sf.is_file() and not args.reset_all:
            data = cm.read_file(sf)
    except OSError as e:
        cm.print_error(e, e.filename)
        continue

    algorithm = sf.suffix.lstrip('.')

    for df in cm.ifiles(d, hidden_files=args.hidden_files):
        if df not in data:
            cm.print_message('NEW', df)
            continue

        if args.only_modified and cm.is_older(df, data[df]['created']):
            continue

        try:
            if data[df]['checksum'] != cm.create_checksum(df, algorithm):
                cm.print_message('BAD', df)
            elif args.verbose:
                cm.print_message('OK', df)
        except OSError as e:
            cm.print_error(e, e.filename)
            
# Checksums

This is a simple script that goes through every directory and writes checksums in common file formats. This is a personal project. I don't guarantee any functionality.

## Usage

### Create

```
usage: checksums-create [-h] [-R] [--include-hidden] [--prefix PREFIX] [--blake2b | --md5 | --sha256 | --sha1 | --sha512] [--reset-all | --reset-modified] PATH

positional arguments:
  PATH

options:
  -h, --help        show this help message and exit
  -R                enable recursion
  --include-hidden  include hidden files and dirs
  --prefix PREFIX   prefix to use for sumfiles
  --blake2b         uses blake2b
  --md5             uses md5
  --sha256          uses sha256
  --sha1            uses sha1
  --sha512          uses sha512
  --reset-all       resets all checksums
  --reset-modified  resets checksums for modified files
```

### Verify
```
usage: checksums-verify [-h] [-R] [--include-hidden] [--prefix PREFIX] [--blake2b | --sha256 | --sha512 | --md5 | --sha1] PATH

positional arguments:
  PATH

options:
  -h, --help        show this help message and exit
  -R                enable recursion
  --include-hidden  include hidden files and dirs
  --prefix PREFIX   prefix to use for sumfiles
  --blake2b         uses blake2b
  --sha256          uses sha256
  --sha512          uses sha512
  --md5             uses md5
  --sha1            uses sha1
```

The default behavior is to ignore files that are already listed in the checksum file. So, this script only appends checksums unless you use the --reset-all or --reset-modified options.

## Examples
```
python create.py -R --sha256 --reset-modified ~\backup
```

Common tools can be used to verify integrity.

```
sha256sum -c ~\backup\.checksums.sha256
```

or

```
python verify.py -Rv --sha256 ~\backup
```
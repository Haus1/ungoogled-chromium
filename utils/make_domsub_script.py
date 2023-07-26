#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright (c) 2023 The ungoogled-chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
Generate standalone script that performs the domain substitution.
"""

from pathlib import Path
import argparse
import re


def make_domain_substitution_script(regex_path, files_path, output_path):
    """
    Generate a standalone shell script (which uses Perl) that performs
        domain substitution on the appropriate files.

    regex_path is a pathlib.Path to domain_regex.list
    files_path is a pathlib.Path to domain_substitution.list
    output_path is a pathlib.Path to the output file.

    Raises FileNotFoundError if the regex or file lists do not exist.
    Raises FileExistsError if the output file already exists.
    """
    if not regex_path.exists():
        raise FileNotFoundError(regex_path)
    if not files_path.exists():
        raise FileNotFoundError(files_path)
    if output_path.exists():
        raise FileExistsError(output_path)

    regex_list = tuple(filter(len, regex_path.read_text().splitlines()))
    files_list = tuple(filter(len, files_path.read_text().splitlines()))

    # Convert the Python-style regexes into a Perl s/// op
    perl_replace_list = ['s#' + re.sub(r'\\g<(\d+)>', r'${\1}', x) + '#g' for x in regex_list]

    files_list_str = '\n'.join(files_list)
    perl_replace_list_str = '\n'.join([f'    {x};' for x in perl_replace_list])

    with open(output_path, 'w') as out:
        out.write("""#!/bin/sh -e
#
# This script performs domain substitution on the Chromium source files.
#
# Generated by make_domsub_script.py, part of the ungoogled-chromium project:
# https://github.com/ungoogled-software/ungoogled-chromium.git
#

# Check that we are inside the Chromium source tree
test -f build/config/compiler/BUILD.gn

# These filenames may contain spaces and/or other unusual characters
print_file_list() {
	cat <<'__END__'
%s
__END__
}

echo "Creating backup archive ..."

backup=domain-substitution.orig.tar
print_file_list | tar cf $backup --verbatim-files-from --files-from=-

echo "Applying ungoogled-chromium domain substitution to %d files ..."

print_file_list | xargs -d '\\n' perl -0777 -C0 -pwi -e '
%s
'

# end
""" % (files_list_str, len(files_list), perl_replace_list_str))


def _callback(args):
    """CLI Callback"""
    make_domain_substitution_script(args.regex, args.files, args.output)


def main():
    """CLI Entrypoint"""
    parser = argparse.ArgumentParser()
    parser.set_defaults(callback=_callback)

    parser.add_argument('-r', '--regex', type=Path, required=True, help='Path to domain_regex.list')
    parser.add_argument(
        '-f', '--files', type=Path, required=True, help='Path to domain_substitution.list')
    parser.add_argument(
        '-o', '--output', type=Path, required=True, help='Path to script file to create')

    args = parser.parse_args()
    args.callback(args)


if __name__ == '__main__':
    main()
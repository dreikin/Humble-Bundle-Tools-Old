import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse

ILLEGAL_NAMES = ['CON',
                 'PRN',
                 'AUX',
                 'NUL',
                 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']


# Makes a path component safe for use on Windows (and probably all other systems).
def make_safe(path_component):
    # See https://msdn.microsoft.com/en-us/library/aa365247.aspx for bad names.
    # Illegal characters are removed, illegal names are deterministically renamed.

    safe_pc = path_component
    # Remove reserved characters.
    safe_pc = re.sub(r'[\\/*?:"<>|]', '', safe_pc)
    safe_pc = re.sub('[\u0000-\u001F]', '', safe_pc)

    # Remove trailing '.' or ' '.
    while safe_pc[-1] == '.' or safe_pc[-1] == ' ':
        safe_pc = safe_pc[:-1]

    # Rename if name not legal.
    if safe_pc.upper().split('.')[0] in ILLEGAL_NAMES:
        safe_pc = '_' + safe_pc

    return safe_pc


def flat_sums(products):
    checksums = []
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                checksum = ds['md5']
                checksums.append(checksum + ' *./' + make_safe(filename))
    return checksums


def folder_sums(products):
    checksums = []
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                folder = product['human_name']
                checksum = ds['md5']
                checksums.append(checksum + ' *./' + make_safe(folder) + '/' + make_safe(filename))
    return checksums


def print_checksums(checksums):
    for checksum in checksums:
        print(checksum)


def write_checksums(checksums, filename):
    fp = open(filename, 'w', newline='\n', encoding='utf-8')
    for checksum in checksums:
        fp.write(checksum + '\n')
    fp.close()


def make_folders(products):
    for product in products:
        dirname = product['human_name']
        os.mkdir(make_safe(dirname))


def parse_args():
    parser = argparse.ArgumentParser()

    # Positional argument: filename
    parser.add_argument("filename", help="The file containing the JSON to work with.")

    # Flag: use automatic folder hierarchy instead of flat listing.
    parser.add_argument("-f", "--folders", help="Use automatic folder hierarchy in output.", action="store_true")

    # Optional argument: write to file
    # Default: print to screen
    parser.add_argument("-o", "--output", help="File to print expected checksums to.")

    # Optional argument: make directories
    # Over-rides checksum calculations, instead making the directories for the files to be put in.
    parser.add_argument("-d", "--mkdirs",
                           help="Make directories for the files to be put in instead of showing checksums",
                           action="store_true")

    args = parser.parse_args()
    return args, parser


def main():
    args, parser = parse_args()

    # Load JSON from file and get the products portion.
    fp = open(args.filename)
    data = json.load(fp)
    fp.close()
    products = data['subproducts']

    # First, make directories if requested.
    if args.mkdirs:
        make_folders(products)

    # Get the checksums in the desired format.
    checksums = folder_sums(products) if args.folders else flat_sums(products)

    # Print checksums to desired output (terminal by default, file otherwise).
    if args.output:
        write_checksums(checksums, args.output)
    else:
        print_checksums(checksums)


if __name__ == "__main__":
    main()
import argparse
import hashlib
import json
import os
import re
from functools import partial
from typing import List
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


class ProductInfo:
    def __init__(self, human_name, filename, checksum):
        self.human_name = human_name
        self.filename = filename
        self.checksum = checksum

        self.safe_human_name = make_safe(human_name)
        self.safe_filename = make_safe(filename)


def get_product_info(data):
    product_info = []
    for product in data['subproducts']:
        for download in product['downloads']:
            for ds in download['download_struct']:
                human_name = product['human_name']
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                checksum = ds['md5']
                info = ProductInfo(human_name,
                                   filename,
                                   checksum)
                product_info.append(info)
    return product_info


def flat_sums(products: List[ProductInfo]):
    checksums = []
    for product in products:
        checksums.append(product.checksum + ' *./' + product.safe_filename)
    return checksums


def folder_sums(products: List[ProductInfo]):
    checksums = []
    for product in products:
        checksums.append(product.checksum + ' *./'
                         + product.safe_human_name + '/'
                         + product.safe_filename)
    return checksums


def print_checksums(checksums):
    for checksum in checksums:
        print(checksum)


def write_checksums(checksums, filename):
    fp = open(filename, 'w', newline='\n', encoding='utf-8')
    for checksum in checksums:
        fp.write(checksum + '\n')
    fp.close()


def make_folders(products: List[ProductInfo]):
    folders = set()
    for product in products:
        folders.add(product.safe_human_name)
    for folder in folders:
        os.mkdir(folder)


def move_items(products: List[ProductInfo]):
    for product in products:
        os.rename(product.safe_filename, product.safe_human_name + "/" + product.safe_filename)


def make_move(products: List[ProductInfo]):
    make_folders(products)
    move_items(products)


class ChecksumItem:
    def __init__(self, filename, binary_mode):
        self.filename = filename
        self.binary_mode = binary_mode
        self._checksum = ""

    def checksum(self):
        if self._checksum == "":
            mode = 'rb' if self.binary_mode else 'r'
            # StackOverflow implementation.
            # See:
            # http://stackoverflow.com/posts/7829658/revisions
            with open(self.filename, mode) as fp:
                md5sum = hashlib.md5()
                for buf in iter(partial(fp.read, 4096), b''):
                    md5sum.update(buf)
            self._checksum = md5sum.hexdigest()
        return self._checksum


def check(checksums):
    items = []
    for line in checksums:
        binary = False  # default is text mode.
        checksum, filename = line.split(' ', 1)
        if filename[0] == '*':
            binary = True  # use binary mode instead.
        filename = filename[1:]
        items.append({'item': ChecksumItem(filename, binary), 'checksum': checksum})

    failed = 0
    succeeded = 0
    for item in items:
        try:
            if item['item'].checksum() == item['checksum']:
                print(item['item'].filename + ": OK")
                succeeded += 1
            else:
                print(item['item'].filename + ": FAILED")
                failed += 1
        except PermissionError as e:
            print("Problem on file '" + item['item'].filename + "'")
            print(e)
            failed += 1

    print("Succeeded: ", succeeded)
    print("Failed: ", failed)


def parse_args():
    parser = argparse.ArgumentParser()

    # Arguments Summary
    # =================
    # filename:
    #   positional, required; the name of the file containing the JSON data.
    # -f, --folders:
    #   flag; Signals to use folder hierarchy instead of assuming all files are in the same directory.
    # -w, --write:
    #   optional: Tells script to write checksums to a file instead of stdout.
    # -p, --print:
    #   optional: Tells script to print checksums to screen.
    # -c, --check
    #   flag; Tells script to verify files against checksums.
    #
    # Exclusive options:
    # -d, --mkdirs:
    #   optional; Tells script to create directories for each product.
    # -a, --automove
    #   optional, Tells script to move each file into its appropriate directory.
    # -m, --makemove
    #   optional; Tells script to do --mkdirs then --automove.

    # Positional argument: filename
    parser.add_argument("filename", help="The file containing the JSON to work with.")

    # Checksum-focused arguments.
    checksum_group = parser.add_argument_group(title="Checksum actions")

    # Optional argument: write to file
    # Default: print to screen
    checksum_group.add_argument("-p",
                                "--print",
                                help="Print expected checksums to console.",
                                action="store_true")

    # Optional argument: write to file
    # Default: print to screen
    checksum_group.add_argument("-w",
                                "--write",
                                help="Write expected checksums to a specified file.",
                                metavar="FILE")

    # Flag: check files against checksums.
    checksum_group.add_argument("-c",
                        "--check",
                        help="Check files against checksums.",
                        action="store_true")

    # General options.
    options_group = parser.add_argument_group(title="Options")

    # Flag: use automatic folder hierarchy instead of flat listing.
    options_group.add_argument("-f",
                               "--folders",
                               help="Use automatic folder hierarchy in output." +
                                    "Turned on automatically if an option moving files into folders is used.",
                               action="store_true")

    # File and folder actions.
    group = parser.add_mutually_exclusive_group()

    # Optional argument: make directories
    # Over-rides checksum calculations, instead making the directories for the files to be put in.
    group.add_argument("-d",
                        "--mkdirs",
                        help="Make directories for the files to be put in instead of showing checksums",
                        action="store_true")

    # Optional argument: move files into directories
    group.add_argument("-a",
                       "--automove",
                       help="Move each file into its appropriate directory.  Assumes directories already exist.",
                       action="store_true")

    # Optional argument: make directories and move the files into matching directories.
    group.add_argument("-m",
                       "--makemove",
                       help="Make directories and then move each file into its appropriate directory.",
                       action="store_true")

    args = parser.parse_args()
    return args, parser


def main():
    args, parser = parse_args()
    work_done = False

    # Load JSON from file and get the products portion.
    fp = open(args.filename)
    data = json.load(fp)
    fp.close()
    products = get_product_info(data)

    # First, do directory and file operations.
    if args.mkdirs:
        make_folders(products)
        work_done = True

    if args.automove:
        args.folders = True
        move_items(products)
        work_done = True

    if args.makemove:
        args.folders = True
        make_move(products)
        work_done = True

    # Get the checksums in the desired format.
    checksums = folder_sums(products) if args.folders else flat_sums(products)

    # Print checksums to desired output, if any.
    if args.write:
        write_checksums(checksums, args.write)
        work_done = True
    if args.print:
        print_checksums(checksums)
        work_done = True

    # Check files against checksums.
    if args.check:
        check(checksums)
        work_done = True

    if not work_done:
        print("Nothing to do.")


if __name__ == "__main__":
    main()

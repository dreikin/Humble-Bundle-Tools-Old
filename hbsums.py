import json
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
def make_safe(pc):
    # See https://msdn.microsoft.com/en-us/library/aa365247.aspx for bad names.
    # Illegal characters are removed, illegal names are deterministically renamed.

    safe_pc = pc
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
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                checksum = ds['md5']
                print(checksum + ' *./' + make_safe(filename))


def folder_sums(products):
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                folder = product['human_name']
                checksum = ds['md5']
                print(checksum + ' *./' + make_safe(folder) + '/' + make_safe(filename))


def main(argv=None):
    if not argv[1]:
        return

    fp = open(argv[1])
    data = json.load(fp)
    products = data['subproducts']

    flat_sums(products)
    print()
    folder_sums(products)

if __name__ == "__main__":
    main(sys.argv)
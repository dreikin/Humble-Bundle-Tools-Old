import sys
import json
from urllib.parse import urlparse


def flat_sums(products):
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                checksum = ds['md5']
                print(checksum + ' *./' + filename)

def folder_sums(products):
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = urlparse(ds['url']['web']).path.split("/")[-1]
                folder = product['human_name']
                checksum = ds['md5']
                print(checksum + ' *./' + folder + '/' + filename)


def main(argv=None):
    if not argv[1]:
        return

    fp = open(argv[1])
    data = json.load(fp)
    products = data['subproducts']

    flat_sums(products)

if __name__ == "__main__":
    main(sys.argv)
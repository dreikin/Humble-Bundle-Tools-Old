import sys
import json


def main(argv=None):
    if not argv[1]:
        return

    fp = open(argv[1])
    data = json.load(fp)
    products = data['subproducts']
    for product in products:
        for download in product['downloads']:
            for ds in download['download_struct']:
                filename = ds['url']['web']
                checksum = ds['md5']
                print(checksum + ' *./' + filename)

if __name__ == "__main__":
    main(sys.argv)
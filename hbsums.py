import sys
import json


def main(argv=None):
    if not argv[1]:
        return

    fp = open(argv[1])
    data = json.load(fp)
    products = data['subproducts']
    for product in products:
        print(product['human_name'] + "\n")

if __name__ == "__main__":
    main(sys.argv)
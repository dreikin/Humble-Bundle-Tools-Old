import sys
import json


def main(argv=None):
    if not argv:
        return

    fp = open(argv[0])
    data = json.load(fp)
    products = data.subproducts
    for product in products:
        print(product.human_name + "\n")

if __name__ == "__main__":
    main(sys.argv)
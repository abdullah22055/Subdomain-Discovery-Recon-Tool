import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--name', help='Your name')
args = parser.parse_args()

print(f"Hello, {args.name}!")

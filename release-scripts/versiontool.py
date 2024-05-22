import argparse
import sys

from packaging.version import Version, InvalidVersion


def undev(version):
    return version.base_version

def bumpdev(version):
    version = Version(version.base_version)
    version_tuple = version.public.split(".")
    version_tuple[-1] = str(int(version_tuple[-1]) + 1)
    new_version = Version(".".join(version_tuple) + ".dev0")
    return new_version.public

def bumpmicro(version):
    split = version.public.split(".")
    split[2] = str(int(split[2]) + 1)
    return ".".join(split)

def main():
    parser = argparse.ArgumentParser(description='Version Tool')
    sp = parser.add_subparsers(dest='command')

    undev_p = sp.add_parser("undev", help="Remove dev suffices from version")
    undev_p.add_argument("version", help="Version to remove dev suffices from")

    bumpdev_p = sp.add_parser("bumpdev", help="Bump version to next dev version")
    bumpdev_p.add_argument("version", help="Version to bump to next dev version")

    bumpmicro_p = sp.add_parser("bumpmicro", help="Bump version to next micro version")
    bumpmicro_p.add_argument("version", help="Version to bump to next micro version")

    args = parser.parse_args()

    try:
        version = Version(args.version)
    except InvalidVersion:
        print("Invalid version: {}".format(args.version))
        sys.exit(1)

    if args.command == "undev":
        print(undev(version))
    elif args.command == "bumpdev":
        print(bumpdev(version))
    elif args.command == "bumpmicro":
        print(bumpmicro(version))


if __name__ == "__main__":
    main()

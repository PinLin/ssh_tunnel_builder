#!/usr/bin/env python3
import argparse
import getpass
import os
import sys

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SUDO = "sudo " if os.getuid() != 0 else ""


class Systemd:
    TEMPLATE_FILE = os.path.join(BASE_DIR, "systemd", "ssh-tunnel.service")
    SERVICE_DIR = "/etc/systemd/system/"

    @classmethod
    def make_tunnel(cls, name, ssh_args):
        with open(cls.TEMPLATE_FILE, "r") as f:
            template = f.read()

        service_name = f"ssh-tunnel-{name}"

        tmp_file = os.path.join("/tmp", f"{service_name}.service")
        with open(tmp_file, "w") as f:
            f.write(
                template.format(username=getpass.getuser(), ssh_args=" ".join(ssh_args))
            )

        print(f"Copy {service_name} to `{cls.SERVICE_DIR}`...")
        assert os.system(f"{SUDO}cp {tmp_file} {cls.SERVICE_DIR}") == 0
        print("Reload systemd daemon...")
        assert os.system(f"{SUDO}systemctl daemon-reload") == 0
        print(f"Enable and start {service_name}...")
        assert os.system(f"{SUDO}systemctl enable {service_name}") == 0
        assert os.system(f"{SUDO}systemctl start {service_name}") == 0

    @classmethod
    def list_tunnels(cls):
        assert os.system("systemctl list-units 'ssh-tunnel-*' --all") == 0

    @classmethod
    def remove_tunnel(cls, name):
        service_name = f"ssh-tunnel-{name}"

        file = os.path.join(cls.SERVICE_DIR, f"{service_name}.service")
        if not os.path.exists(file):
            print(f"Service `{service_name}` is not existed.")
            sys.exit(1)

        print(f"Stop and disable {service_name}...")
        assert os.system(f"{SUDO}systemctl stop {service_name}") == 0
        assert os.system(f"{SUDO}systemctl disable {service_name}") == 0
        print(f"Remove {service_name} from `{cls.SERVICE_DIR}`...")
        assert os.system(f"{SUDO}rm {file}") == 0
        print("Reload systemd daemon...")
        assert os.system(f"{SUDO}systemctl daemon-reload") == 0


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=parser.print_help)

    subparsers = parser.add_subparsers(dest="command")
    parser_make = subparsers.add_parser("make", help="make tunnel")
    parser_make.add_argument("name", help="tunnel name")
    parser_make.add_argument("ssh_args", nargs=argparse.REMAINDER, help="ssh arguments")
    subparsers.add_parser("list", help="list tunnels")
    parser_remove = subparsers.add_parser("remove", help="remove tunnel")
    parser_remove.add_argument("name", help="tunnel name")

    args = parser.parse_args()

    if args.command == "make":
        Systemd.make_tunnel(args.name, args.ssh_args)
    elif args.command == "list":
        Systemd.list_tunnels()
    elif args.command == "remove":
        Systemd.remove_tunnel(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

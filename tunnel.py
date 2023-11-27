#!/usr/bin/env python3
import argparse
import getpass
import os
import platform
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
        filename = f"{service_name}.service"

        tmp_file = os.path.join("/tmp", filename)
        with open(tmp_file, "w") as f:
            f.write(
                template.format(username=getpass.getuser(), ssh_args=" ".join(ssh_args))
            )

        print(f"Copy {service_name} to `{cls.SERVICE_DIR}`...")
        assert os.system(f"{SUDO}cp {tmp_file} {cls.SERVICE_DIR}") == 0
        print("Reload systemd daemon...")
        assert os.system(f"{SUDO}systemctl daemon-reload") == 0
        print(f"Start {service_name}...")
        assert os.system(f"{SUDO}systemctl enable {service_name}") == 0
        assert os.system(f"{SUDO}systemctl start {service_name}") == 0

    @classmethod
    def list_tunnels(cls):
        os.system("systemctl list-units 'ssh-tunnel-*' --all")

    @classmethod
    def remove_tunnel(cls, name):
        service_name = f"ssh-tunnel-{name}"
        filename = f"{service_name}.service"

        file = os.path.join(cls.SERVICE_DIR, filename)
        if not os.path.exists(file):
            print(f"Service `{service_name}` is not existed.")
            sys.exit(1)

        print(f"Stop {service_name}...")
        assert os.system(f"{SUDO}systemctl stop {service_name}") == 0
        assert os.system(f"{SUDO}systemctl disable {service_name}") == 0
        print(f"Remove {service_name} from `{cls.SERVICE_DIR}`...")
        assert os.system(f"{SUDO}rm {file}") == 0
        print("Reload systemd daemon...")
        assert os.system(f"{SUDO}systemctl daemon-reload") == 0


class Launchd:
    TEMPLATE_FILE = os.path.join(BASE_DIR, "launchd", "com.ssh-tunnel.plist")
    SERVICE_DIR = "/Library/LaunchDaemons/"

    @classmethod
    def make_tunnel(cls, name, ssh_args):
        with open(cls.TEMPLATE_FILE, "r") as f:
            template = f.read()

        service_name = f"ssh-tunnel-{name}"
        filename = f"com.{service_name}.plist"

        tmp_file = os.path.join("/tmp", filename)
        with open(tmp_file, "w") as f:
            f.write(
                template.format(
                    username=getpass.getuser(),
                    service_name=service_name,
                    ssh_args="</string>\n        <string>".join(ssh_args),
                )
            )
        file = os.path.join(cls.SERVICE_DIR, filename)

        print(f"Copy {service_name} to `{cls.SERVICE_DIR}`...")
        assert os.system(f"{SUDO}cp {tmp_file} {cls.SERVICE_DIR}") == 0
        print(f"Start {service_name}...")
        assert os.system(f"{SUDO}launchctl load -w {file}") == 0

    @classmethod
    def list_tunnels(cls):
        os.system(f"{SUDO}launchctl list | grep com.ssh-tunnel-")

    @classmethod
    def remove_tunnel(cls, name):
        service_name = f"ssh-tunnel-{name}"
        filename = f"com.{service_name}.plist"

        file = os.path.join(cls.SERVICE_DIR, filename)
        if not os.path.exists(file):
            print(f"Service `{service_name}` is not existed.")
            sys.exit(1)

        print(f"Stop {service_name}...")
        assert os.system(f"{SUDO}launchctl unload -w {file}") == 0
        print(f"Remove {service_name} from `{cls.SERVICE_DIR}`...")
        assert os.system(f"{SUDO}rm {file}") == 0


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

    os_type = platform.system()
    if os_type == "Darwin":
        if args.command == "make":
            Launchd.make_tunnel(args.name, args.ssh_args)
        elif args.command == "list":
            Launchd.list_tunnels()
        elif args.command == "remove":
            Launchd.remove_tunnel(args.name)
        else:
            parser.print_help()

    else:
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

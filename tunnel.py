#!/usr/bin/env python
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

        service_name = "ssh-tunnel-{}".format(name)
        filename = "{}.service".format(service_name)

        tmp_file = os.path.join("/tmp", filename)
        with open(tmp_file, "w") as f:
            f.write(
                template.format(username=getpass.getuser(), ssh_args=" ".join(ssh_args))
            )

        print("Copy {} to `{}`...".format(service_name, cls.SERVICE_DIR))
        assert os.system("{}cp {} {}".format(SUDO, tmp_file, cls.SERVICE_DIR)) == 0
        print("Reload systemd daemon...")
        assert os.system("{}systemctl daemon-reload".format(SUDO)) == 0
        print("Start {}...".format(service_name))
        assert os.system("{}systemctl enable {}".format(SUDO, service_name)) == 0
        assert os.system("{}systemctl start {}".format(SUDO, service_name)) == 0

    @classmethod
    def list_tunnels(cls):
        os.system("systemctl list-units 'ssh-tunnel-*' --all")

    @classmethod
    def remove_tunnel(cls, name):
        service_name = "ssh-tunnel-{}".format(name)
        filename = "{}.service".format(service_name)

        file = os.path.join(cls.SERVICE_DIR, filename)
        if not os.path.exists(file):
            print("Service `{}` is not existed.".format(service_name))
            sys.exit(1)

        print("Stop {}...".format(service_name))
        assert os.system("{}systemctl stop {}".format(SUDO, service_name)) == 0
        assert os.system("{}systemctl disable {}".format(SUDO, service_name)) == 0
        print("Remove {} from `{}`...".format(service_name, cls.SERVICE_DIR))
        assert os.system("{}rm {}".format(SUDO, file)) == 0
        print("Reload systemd daemon...")
        assert os.system("{}systemctl daemon-reload".format(SUDO)) == 0


class Launchd:
    TEMPLATE_FILE = os.path.join(BASE_DIR, "launchd", "com.ssh-tunnel.plist")
    SERVICE_DIR = "/Library/LaunchDaemons/"

    @classmethod
    def make_tunnel(cls, name, ssh_args):
        with open(cls.TEMPLATE_FILE, "r") as f:
            template = f.read()

        service_name = "ssh-tunnel-{}".format(name)
        filename = "com.{}.plist".format(service_name)

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

        print("Copy {} to `{}`...".format(service_name, cls.SERVICE_DIR))
        assert os.system("{}cp {} {}".format(SUDO, tmp_file, cls.SERVICE_DIR)) == 0
        print("Start {}...".format(service_name))
        assert os.system("{}launchctl load -w {}".format(SUDO, file)) == 0

    @classmethod
    def list_tunnels(cls):
        os.system("{}launchctl list | grep com.ssh-tunnel-".format(SUDO))

    @classmethod
    def remove_tunnel(cls, name):
        service_name = "ssh-tunnel-{}".format(name)
        filename = "com.{}.plist".format(service_name)

        file = os.path.join(cls.SERVICE_DIR, filename)
        if not os.path.exists(file):
            print("Service `{}` is not existed.".format(service_name))
            sys.exit(1)

        print("Stop {}...".format(service_name))
        assert os.system("{}launchctl unload -w {}".format(SUDO, file)) == 0
        print("Remove {} from `{}`...".format(service_name, cls.SERVICE_DIR))
        assert os.system("{}rm {}".format(SUDO, file)) == 0


COMMAND_ALIASES = {"make": "new", "list": "ls", "remove": "rm"}


def add_new_parser(subparsers, name, **kwargs):
    parser = subparsers.add_parser(name, **kwargs)
    parser.add_argument("name", help="tunnel name")
    parser.add_argument("ssh_args", nargs=argparse.REMAINDER, help="ssh arguments")
    return parser


def add_rm_parser(subparsers, name, **kwargs):
    parser = subparsers.add_parser(name, **kwargs)
    parser.add_argument("name", help="tunnel name")
    return parser


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=parser.print_help)

    subparsers = parser.add_subparsers(dest="command", metavar="{new,ls,rm}")
    add_new_parser(subparsers, "new", help="make tunnel")
    subparsers.add_parser("ls", help="list tunnels")
    add_rm_parser(subparsers, "rm", help="remove tunnel")

    # Deprecated command names, kept for backward compatibility.
    # Omitting `help` keeps them out of the help listing.
    add_new_parser(subparsers, "make")
    subparsers.add_parser("list")
    add_rm_parser(subparsers, "remove")

    args = parser.parse_args()

    command = COMMAND_ALIASES.get(args.command, args.command)

    backend = Launchd if platform.system() == "Darwin" else Systemd
    if command == "new":
        backend.make_tunnel(args.name, args.ssh_args)
    elif command == "ls":
        backend.list_tunnels()
    elif command == "rm":
        backend.remove_tunnel(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

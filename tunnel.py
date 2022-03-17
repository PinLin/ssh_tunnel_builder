#!/usr/bin/env python3
import os
import json
import argparse


def create_systemd_service(name, user, rule, destination):
    content = """
[Unit]
Description=Service Tunnel
After=network.target

[Service]
Type=simple
User={USER}
Restart=always
RestartSec=1
StartLimitInterval=0
ExecStart=/usr/bin/env ssh -o "ExitOnForwardFailure yes" -NR {ADDRESS} {DESTINATION}

[Install]
WantedBy=multi-user.target
    """.format(USER=user, ADDRESS=rule, DESTINATION=destination)

    with open('/etc/systemd/system/' + name + '.service', 'w') as f:
        f.write(content)

    os.system('systemctl daemon-reload')


def clear_tunnels():
    if (os.getuid() != 0):
        print("You must be root to run this script")
        return

    for filename in os.listdir('/etc/systemd/system'):
        if (not 'ssh_tunnel_' in filename) and (not 'service_tunnel_' in filename):
            continue

        service_name = filename.split('.')[0]

        os.system('systemctl stop ' + service_name)
        os.system('systemctl disable ' + service_name)

        if os.path.isfile('/etc/systemd/system/' + service_name + '.service'):
            os.remove('/etc/systemd/system/' + service_name + '.service')

    os.system('systemctl daemon-reload')


def build_tunnels():
    if (os.getuid() != 0):
        print("You must be root to run this script")
        return

    with open('config.json') as f:
        config = json.load(f)

    user = config['user']
    destination = config['destination']

    for tunnel in config['tunnels']:
        name = tunnel['name']
        rule = tunnel['rule']
        service_name = 'ssh_tunnel_' + '_'.join(name.lower().split())

        if os.path.isfile('/etc/systemd/system/' + service_name + '.service'):
            continue

        create_systemd_service(service_name, user, rule, destination)

        os.system('systemctl enable ' + service_name)
        os.system('systemctl start ' + service_name)


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=parser.print_help)

    subparsers = parser.add_subparsers()
    parser_build = subparsers.add_parser(
        'build', help='build tunnels if it is not existed')
    parser_build.set_defaults(func=build_tunnels)
    parser_clear = subparsers.add_parser(
        'clear', help='clear all existed tunnels')
    parser_clear.set_defaults(func=clear_tunnels)

    args = parser.parse_args()
    args.func()


if __name__ == '__main__':
    main()

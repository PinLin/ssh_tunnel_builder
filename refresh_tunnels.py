#!/usr/bin/env python3
import os
import sys

from config import TUNNELS


SERVICE_DIRECTORY = os.getenv('SERVICE_DIRECTORY', '/etc/systemd/system')


def stop_and_remove_tunnels():
    """
    停止所有的 tunnels 服務
    """
    for filename in os.listdir(SERVICE_DIRECTORY):
        if not 'service_tunnel' in filename:
            continue

        filename = filename.split('.')[0]

        os.system(f'systemctl stop {filename}')
        os.system(f'systemctl disable {filename}')

        if os.path.isfile(f'{SERVICE_DIRECTORY}/{filename}.service'):
            os.remove(f'{SERVICE_DIRECTORY}/{filename}.service')

    os.system('systemctl daemon-reload')


def create_and_start_tunnels():
    """
    重新建立並啟動 tunnels 服務
    """
    with open(sys.path[0] + '/templates/service_tunnel.service') as f:
        template = f.read()

    for tunnel in TUNNELS:
        description = tunnel['description']
        user = tunnel['user']
        address = tunnel['address']
        destination = tunnel['destination']
        filename = 'service_tunnel_' + '_'.join(description.lower().split())

        with open(f'{SERVICE_DIRECTORY}/{filename}.service', 'w') as f:
            f.write(template.format(DESCRIPTION=description,
                                    USER=user,
                                    ADDRESS=address,
                                    DESTINATION=destination,
                                    FILENAME=filename))

        os.system('systemctl daemon-reload')
        os.system(f'systemctl enable {filename}')
        os.system(f'systemctl start {filename}')


def main():
    stop_and_remove_tunnels()
    create_and_start_tunnels()


if __name__ == '__main__':
    main()

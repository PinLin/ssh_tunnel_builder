# SSH Tunnel Builder

用來建立 SSH Tunnel 系統服務的小工具，建立的服務會在開機時建立 SSH Tunnel 並在斷線時自動重連。

## Supported Init Systems

- Systemd
- Launchd

## Usage

建立 SSH Tunnel 服務：

```bash
python3 tunnel.py new <tunnel_name> <ssh_args>
```

> 例如：
> ```bash
> python3 tunnel.py new mariadb remote_user@remote_host -R 3306:localhost:3306
> ```

列出既有的 SSH Tunnel 服務：

```bash
python3 tunnel.py ls
```

移除 SSH Tunnel 服務：

```bash
python3 tunnel.py rm <tunnel_name>
```

> 舊的指令名稱 `make`、`list`、`remove` 仍可使用。

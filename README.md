# Mikrotik-SSH-backup
Automatically create binary backups and configuration exports of Mikrotik
RouterOS devices via SSH.


## Installation
It is recommended to use [`pipx`](https://github.com/pypa/pipx) for
installing standalone applications:
```sh
pipx install git+https://github.com/ondras12345/mikrotik-ssh-backup.git
```
(However, `pip` should also work.)


## Setup
Only public key SSH authentication is supported.
Add an entry to your `~/.ssh/config` file:
```
Host my_router
    User <username>
    Hostname <ip address>
    Port <port>
    # optional: use a different private key file.
    #IdentityFile ~/.ssh/id_rsa
```

You should now be able to connect to the router using this command:
```sh
ssh my_router
```

Create a configuration file:
```sh
cd ~/directory_with_mikrotik_backups
cat << EOF > mikrotik.yaml
routers:
  my_router:
EOF
```
(see `mikrotik-ssh-backup print_config` for all options.)

Create a binary backup and an rsc export:
```console
$ mikrotik-ssh-backup backup --export --backup my_router
exporting
export written to tracked/my_router_20240607T230237.rsc
copying to repo
making binary backup
Configuration backup saved
downloading
autobak.backup                                   100%  153KB   4.3MB/s   00:00
binary backup written to tracked/my_router_20240607T230237.backup size: 156213
done
```

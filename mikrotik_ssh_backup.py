#!/usr/bin/env python3

import argparse
import subprocess
import datetime
import os
import sys
import shutil
import yaml
from pathlib import Path
from dataclasses import dataclass
from pprint import pprint


@dataclass
class Router:
    ssh_host: str
    filename_prefix: str
    # default for RouterOS 7
    export_command: str = "/export show-sensitive"
    backup_command: str = "/system/backup save name=autobak dont-encrypt=yes"


def list_routers(config):
    pprint(config["routers"])


def print_config(config):
    print(yaml.dump(config))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-C", "--config-file",
        help="path to configuration file (default: %(default)s)",
        type=argparse.FileType("r"),
        default="./mikrotik.yaml"
    )

    subparsers = parser.add_subparsers(dest="subparser_name", required=True)

    subparsers.add_parser(
        "list_routers",
        help="list available routers from config file and exit"
    )

    subparsers.add_parser(
        "print_config",
        help="dump current config (incl. defaults) as yaml to stdout and exit"
    )

    parser_backup = subparsers.add_parser(
        "backup",
        help="perform backup"
    )

    parser_backup.add_argument(
        "-d", "--diff",
        help="Do not backup, just diff exports",
        action="store_true"
    )

    parser_backup.add_argument(
        "-e", "--export",
        help="Make export (text script) backup",
        action="store_true"
    )

    parser_backup.add_argument(
        "-b", "--backup",
        help="Make binary backup",
        action="store_true"
    )

    parser_backup.add_argument(
        "router",
        help="router name (see list_routers)"
    )

    args = parser.parse_args()

    with args.config_file as f:
        config = yaml.safe_load(f)

        config["tracked_dir"] = Path(config.get("tracked_dir", "tracked"))
        config["repo_dir"] = Path(config.get("repo_dir", "."))

        for router_name, cnf in config["routers"].items():
            if cnf is None:
                cnf = {}
            router = Router(
                ssh_host=cnf.get("ssh_host", router_name),
                filename_prefix=cnf.get("filename_prefix", router_name),
            )
            if "backup_command" in cnf:
                router.backup_command = cnf["backup_command"]
            if "export_command" in cnf:
                router.export_command = cnf["export_command"]
            config["routers"][router_name] = router

    if args.subparser_name == "list_routers":
        list_routers(config)
        sys.exit(0)

    if args.subparser_name == "print_config":
        print_config(config)
        sys.exit(0)

    if args.router not in config["routers"]:
        parser_backup.error(f"unknown router: {args.router}")

    router = config["routers"][args.router]

    if args.diff:
        subprocess.run(
            f'ssh {router.ssh_host} "{router.export_command}" | '
            f'diff --color -u "{router.filename_prefix}.rsc" -',
            shell=True
        )
        sys.exit(0)

    time_suffix = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    config["tracked_dir"].mkdir(parents=True, exist_ok=True)
    filename_rsc = config["tracked_dir"] / f"{router.filename_prefix}_{time_suffix}.rsc"
    filename_binary = config["tracked_dir"] / f"{router.filename_prefix}_{time_suffix}.backup"

    if args.export:
        print("exporting")
        with open(filename_rsc, 'w') as f:
            subprocess.run(
                ["ssh", router.ssh_host, router.export_command],
                stdout=f
            )
        print("export written to", filename_rsc)

        print("copying to repo")
        shutil.copyfile(filename_rsc, config["repo_dir"] / (router.filename_prefix + ".rsc"))

    if args.backup:
        print("making binary backup")
        subprocess.run(
            ["ssh", router.ssh_host, router.backup_command]
        )
        print("downloading")
        subprocess.run(
            ["scp", router.ssh_host+":/autobak.backup", filename_binary]
        )
        print("binary backup written to", filename_binary,
              "size:", os.stat(filename_binary).st_size)

    print("done")


if __name__ == "__main__":
    main()

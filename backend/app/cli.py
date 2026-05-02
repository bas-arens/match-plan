# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/cli.py
# Author:  Bas Arens
# Purpose: Tiny admin CLI for managing users in app/data/users.json.
#          Used to seed initial admin accounts before the JSON→DB migration.
#
# Usage:
#   python -m app.cli create-user EMAIL [--name NAME] [--password PWD]
#   python -m app.cli list-users
#   python -m app.cli delete-user EMAIL
#
# If --password is omitted, the command prompts for it on stdin without echo.
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import getpass
import sys

from app.services.users import (
    find_user_by_email,
    hash_password,
    load_users,
    save_users,
)


def cmd_create_user(args: argparse.Namespace) -> int:
    email = args.email.strip().lower()
    if find_user_by_email(email):
        print(f"User already exists: {email}", file=sys.stderr)
        return 1

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        return 1

    users = load_users()
    users.append({
        "email": email,
        "name": args.name,
        "password_hash": hash_password(password),
    })
    save_users(users)
    print(f"Created user: {email}")
    return 0


def cmd_list_users(_: argparse.Namespace) -> int:
    users = load_users()
    if not users:
        print("(no users)")
        return 0
    for u in users:
        print(f"{u['email']}\t{u.get('name') or ''}")
    return 0


def cmd_delete_user(args: argparse.Namespace) -> int:
    email = args.email.strip().lower()
    users = load_users()
    remaining = [u for u in users if u.get("email", "").lower() != email]
    if len(remaining) == len(users):
        print(f"No such user: {email}", file=sys.stderr)
        return 1
    save_users(remaining)
    print(f"Deleted user: {email}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="MatchPlan admin CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create-user", help="Create a new admin user")
    p_create.add_argument("email")
    p_create.add_argument("--name", default=None)
    p_create.add_argument("--password", default=None, help="If omitted, prompt securely")
    p_create.set_defaults(func=cmd_create_user)

    p_list = sub.add_parser("list-users", help="List all users")
    p_list.set_defaults(func=cmd_list_users)

    p_delete = sub.add_parser("delete-user", help="Delete a user by email")
    p_delete.add_argument("email")
    p_delete.set_defaults(func=cmd_delete_user)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

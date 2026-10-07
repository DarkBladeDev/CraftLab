"""
Seeds data/auth.db with default test accounts across all RBAC roles.
Usage:
    python scripts/seed_dev_auth.py
"""
import sys
from pathlib import Path

# Add CraftLab-ctl src to sys.path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "CraftLab-ctl" / "src"))

from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.auth import Role, create_user, list_users


DEV_USERS = [
    {
        "username": "admin",
        "password": "AdminPassword123!",
        "display_name": "System Administrator",
        "roles": [Role.ADMIN.value],
    },
    {
        "username": "operator",
        "password": "OperatorPassword123!",
        "display_name": "Operations Lead",
        "roles": [Role.OPERATOR.value],
    },
    {
        "username": "creator",
        "password": "CreatorPassword123!",
        "display_name": "Content Creator",
        "roles": [Role.CREATOR.value],
    },
    {
        "username": "viewer",
        "password": "ViewerPassword123!",
        "display_name": "Auditor / Read-Only",
        "roles": [Role.VIEWER.value],
    },
]


def main():
    paths = get_paths()
    print(f"[*] Initializing auth database at: {paths.auth_db_path}")

    for user_info in DEV_USERS:
        u = create_user(
            paths.auth_db_path,
            username=user_info["username"],
            password=user_info["password"],
            display_name=user_info["display_name"],
            roles=user_info["roles"],
        )
        print(f"  [+] User created/updated: {u.username} (roles: {', '.join(u.roles)})")

    print(f"\n[v] Successfully seeded {len(DEV_USERS)} development users.\n")
    print("Test credentials summary:")
    print("-" * 55)
    for user_info in DEV_USERS:
        print(f"Username: {user_info['username']:10} | Password: {user_info['password']:20} | Role: {user_info['roles'][0]}")
    print("-" * 55)


if __name__ == "__main__":
    main()

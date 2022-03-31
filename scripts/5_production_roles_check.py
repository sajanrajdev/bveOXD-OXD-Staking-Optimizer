from brownie import network, interface, web3
from _setup.config import REGISTRY
from helpers.constants import AddressZero
from rich.console import Console
from tabulate import tabulate

console = Console()

DEFAULT_ADMIN_ROLE = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)

table_head = ["Role", "MemberCount", "Address"]


def main():
    """
    Checks that the proxyAdmin of all conracts added to the BadgerRegistry match
    the proxyAdminTimelock address on the same registry. How to run:

    1. Add all keys to check paired to the key of the expected DEFAULT_ADMIN_ROLE to the
       'keys_with_admins' array.

    2. Add an array with all the expected roles belonging to each one of the keyed contracts
       added on the previous step to the 'roles' array. The index of the key must match the index
       of its roles array.

    3. Run the script and analyze the printed results.
    """

    console.print("You are using the", network.show_active(), "network")

    # Get production registry
    registry = interface.IBadgerRegistry(REGISTRY)

    # NOTE: Add keys to check paired to the key of their expected DEFAULT_ADMIN_ROLE:
    keys_with_admins = [
        ["badgerTree", "governance"],
        ["BadgerRewardsManager", "governance"],
        ["rewardsLogger", "governance"],
        ["keeper", "devGovernance"],
    ]

    # NOTE: Add all the roles related to the keys to check from the previous array. Indexes must match!
    roles = [
        [
            "DEFAULT_ADMIN_ROLE",
            "ROOT_PROPOSER_ROLE",
            "ROOT_VALIDATOR_ROLE",
            "PAUSER_ROLE",
            "UNPAUSER_ROLE",
        ],
        ["DEFAULT_ADMIN_ROLE", "SWAPPER_ROLE", "DISTRIBUTOR_ROLE"],
        ["DEFAULT_ADMIN_ROLE", "MANAGER_ROLE"],
        ["DEFAULT_ADMIN_ROLE", "EARNER_ROLE", "HARVESTER_ROLE", "TENDER_ROLE"],
    ]

    assert len(keys_with_admins) == len(roles)

    check_roles(registry, keys_with_admins, roles)


def check_roles(registry, keys_with_admins, roles):
    for key in keys_with_admins:
        console.print("[blue]Checking roles for[/blue]", key[0])

        # Get contract address
        contract = registry.get(key[0])
        admin = registry.get(key[1])

        if contract == AddressZero:
            console.print("[red]Key not found on registry![/red]")
            continue

        table_data = []

        access_control = interface.IAccessControl(contract)

        keyRoles = roles[keys_with_admins.index(key)]
        hashes = get_roles_hashes(keyRoles)

        for role in keyRoles:
            role_hash = hashes[keyRoles.index(role)]
            role_member_count = access_control.getRoleMemberCount(role_hash)
            if role_member_count == 0:
                table_data.append([role, "-", "No Addresses found for this role"])
            else:
                for member_number in range(role_member_count):
                    member_address = access_control.getRoleMember(role_hash, member_number)
                    if role == "DEFAULT_ADMIN_ROLE":
                        if member_address == admin:
                            console.print(
                                "[green]DEFAULT_ADMIN_ROLE matches[/green]",
                                key[1],
                                admin,
                            )
                        else:
                            console.print(
                                "[red]DEFAULT_ADMIN_ROLE doesn't match[/red]",
                                key[1],
                                admin,
                            )
                    table_data.append([role, member_number, member_address])

        print(tabulate(table_data, table_head, tablefmt="grid"))


def get_roles_hashes(roles):
    hashes = []
    for role in roles:
        if role == "DEFAULT_ADMIN_ROLE":
            hashes.append(DEFAULT_ADMIN_ROLE)
        else:
            hashes.append(web3.keccak(text=role).hex())

    return hashes

from brownie import interface, network, TheVault, web3
from _setup.config import REGISTRY
from helpers.constants import AddressZero
from rich.console import Console

console = Console()

ADMIN_SLOT = int(0xB53127684A568B3173AE13B9F8A6016E243E63B6E8EE1178D6A717850B5D6103)


def main():
    """
    Checks that the proxyAdmin of all conracts added to the BadgerRegistry match
    the proxyAdminTimelock address on the same registry. How to run:

    1. Add all keys for the network's registry to the 'keys' array below.

    2. Add all authors' addresses with vaults added to the registry into the 'authors' array below.

    3. Add all all keys for the proxyAdmins for the network's registry paired to their owners' keys.

    4. Run the script and review the console output.
    """

    console.print("You are using the", network.show_active(), "network")

    # Get production registry
    registry = interface.IBadgerRegistry(REGISTRY)

    # Get proxyAdminTimelock
    proxy_admin = registry.get("proxyAdminTimelock")
    assert proxy_admin != AddressZero
    console.print("[cyan]proxyAdminTimelock:[/cyan]", proxy_admin)

    # NOTE: Add all existing keys from your network's registry. For example:
    keys = [
        "governance",
        "guardian",
        "keeper",
        "badgerTree",
        "devGovernance",
        "paymentsGovernance",
        "governanceTimelock",
        "proxyAdminDev",
        "rewardsLogger",
        "keeperAccessControl",
        "proxyAdminDfdBadger",
        "dfdBadgerSharedGovernance",
    ]

    # NOTE: Add all authors from your network's registry. For example:
    authors = ["0xee8b29aa52dd5ff2559da2c50b1887adee257556"]

    # NOTE: Add the keys to all proxyAdmins from your network's registry paired to their owner
    proxy_admin_owners = [
        ["proxyAdminTimelock", "governanceTimelock"],
        ["proxyAdminDev", "devGovernance"],
        ["proxyAdminDfdBadger", "dfdBadgerSharedGovernance"],
    ]

    check_by_keys(registry, proxy_admin, keys)
    check_vaults_and_strategies(registry, proxy_admin, authors)
    check_proxy_admin_owners(proxy_admin_owners, registry)


def check_by_keys(registry, proxy_admin, keys):
    console.print("[blue]Checking proxyAdmins by key...[/blue]")
    # Check the proxyAdmin of the different proxy contracts
    for key in keys:
        proxy = registry.get(key)
        if proxy == AddressZero:
            console.print(key, ":[red] key doesn't exist on the registry![/red]")
            continue
        check_proxy_admin(proxy, proxy_admin, key)


def check_vaults_and_strategies(registry, proxy_admin, authors):
    console.print("[blue]Checking proxyAdmins from vaults and strategies...[/blue]")

    vault_status = [0, 1, 2]

    vaults = []
    strategies = []
    strat_names = []

    # get vaults by author
    for author in authors:
        vaults += registry.getVaults("v1", author)
        vaults += registry.getVaults("v2", author)

    # Get promoted vaults
    for status in vault_status:
        vaults += registry.getFilteredProductionVaults("v1", status)
        vaults += registry.getFilteredProductionVaults("v2", status)

    # Get strategies from vaults and check vaults' proxyAdmins
    for vault in vaults:
        try:
            vault_contract = TheVault.at(vault)
            strategies.append(vault_contract.strategy())
            strat_names.append(vault_contract.name().replace("Badger Sett ", "Strategy "))
            # Check vault proxyAdmin
            check_proxy_admin(vault, proxy_admin, vault_contract.name())
        except Exception as error:
            print("Something went wrong")
            print(error)

    for strat in strategies:
        try:
            # Check strategies' proxyAdmin
            check_proxy_admin(strat, proxy_admin, strat_names[strategies.index(strat)])
        except Exception as error:
            print("Something went wrong")
            print(error)


def check_proxy_admin(proxy, proxy_admin, key):
    # Get proxyAdmin address form the proxy's ADMIN_SLOT
    val = web3.eth.getStorageAt(proxy, ADMIN_SLOT).hex()
    address = "0x" + val[26:66]

    # Check differnt possible scenarios
    if address == AddressZero:
        console.print(key, ":[red] admin not found on slot (GnosisSafeProxy?)[/red]")
    elif address != proxy_admin:
        console.print(
            key, ":[red] admin is different to proxyAdminTimelock[/red] - ", address
        )
    else:
        assert address == proxy_admin
        console.print(key, ":[green] admin matches proxyAdminTimelock![/green]")


def check_proxy_admin_owners(proxy_admin_owners, registry):
    console.print("[blue]Checking proxyAdmins' owners...[/blue]")

    for admin_owner_pair in proxy_admin_owners:
        proxy_admin = registry.get(admin_owner_pair[0])
        owner = registry.get(admin_owner_pair[1])
        # Get proxyAdmin's owner address from slot 0
        val = web3.eth.getStorageAt(proxy_admin, 0).hex()
        address = "0x" + val[26:66]

        # Check differnt possible scenarios
        if address == AddressZero:
            console.print(admin_owner_pair[0], ":[red] no address found at slot 0![/red]")
        elif address != owner:
            console.print(
                admin_owner_pair[0],
                ":[red] owner is different to[/red]",
                admin_owner_pair[1],
                "-",
                address,
            )
        else:
            assert address == owner
            console.print(
                admin_owner_pair[0],
                ":[green] owner matches[/green]",
                admin_owner_pair[1],
            )

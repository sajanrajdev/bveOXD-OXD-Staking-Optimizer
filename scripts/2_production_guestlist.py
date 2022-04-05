import time

from brownie import (
    accounts,
    network,
    AdminUpgradeabilityProxy,
    TheGuestlist,
    interface,
    TheVault,
)

from _setup.config import REGISTRY

from helpers.constants import AddressZero

import click
from rich.console import Console

console = Console()

sleep_between_tx = 1


def main():
    """
    FOR PRODUCTION
    Deploys a guestlist contract, sets its parameters and assigns it to an specific vault.
    Additionally, the script transfers the guestlist's ownership to the Badger Governance.
    IMPORTANT: Must input the desired vault address to add the guestlist to as well as the
    different guestlist parameters below.
    """

    # NOTE: Input your vault address and guestlist parameters below:
    vault_addr = "0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"
    merkle_root = "0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"
    user_cap = 2e18
    total_cap = 50e18

    # Get deployer account from local keystore. Deployer must be the
    # vault's governance address in order to set its guestlist parameters.
    dev = connect_account()

    # Get actors from registry
    registry = interface.IBadgerRegistry(REGISTRY)

    governance = registry.get("governance")
    proxy_admin = registry.get("proxyAdminTimelock")

    assert governance != AddressZero
    assert proxy_admin != AddressZero

    # Deploy guestlist
    guestlist = deploy_guestlist(dev, proxy_admin, vault_addr)

    # Set guestlist parameters
    guestlist.setUserDepositCap(user_cap, {"from": dev})
    assert guestlist.userDepositCap() == user_cap

    guestlist.setTotalDepositCap(total_cap, {"from": dev})
    assert guestlist.totalDepositCap() == total_cap

    guestlist.setGuestRoot(merkle_root, {"from": dev})
    assert guestlist.guestRoot() == merkle_root

    # Transfers ownership of guestlist to Badger Governance
    guestlist.transferOwnership(governance, {"from": dev})
    assert guestlist.owner() == governance

    # Sets guestlist on Vault (Requires dev == Vault's governance)
    vault = TheVault.at(vault_addr)
    vault.setGuestList(guestlist.address, {"from": dev})


def deploy_guestlist(dev, proxy_admin, vault_addr):

    guestlist_logic = TheGuestlist.at(
        "0x90A768B0bFF5e4e64f220832fc34f727CCE44d64"
    )  # Guestlist Logic

    # Initializing arguments
    args = [vault_addr]

    guestlist_proxy = AdminUpgradeabilityProxy.deploy(
        guestlist_logic,
        proxy_admin,
        guestlist_logic.initialize.encode_input(*args),
        {"from": dev},
    )
    time.sleep(sleep_between_tx)

    ## We delete from deploy and then fetch again so we can interact
    AdminUpgradeabilityProxy.remove(guestlist_proxy)
    guestlist_proxy = TheGuestlist.at(guestlist_proxy.address)

    console.print("[green]Guestlist was deployed at: [/green]", guestlist_proxy.address)

    return guestlist_proxy


def connect_account():
    click.echo(f"You are using the '{network.show_active()}' network")
    dev = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))
    click.echo(f"You are using: 'dev' [{dev.address}]")
    return dev

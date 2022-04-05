import time

from brownie import accounts, interface, network, StrategybveOxdOxdStakingOptimizer, TheVault

from _setup.config import DEPLOYED_STRAT_ADDR, DEPLOYED_VAULT_ADDR, WANT, REGISTRY

from helpers.constants import AddressZero

import click
from rich.console import Console

console = Console()

sleep_between_tx = 1


def main():
    """
    TO BE RUN BEFORE PROMOTING TO PROD

    Checks and Sets all Keys for Vault and Strategy Against the Registry

    1. Checks all Keys
    2. Sets all Keys

    In case of a mismatch, the script will execute a transaction to change the parameter to the proper one.

    Notice that, as a final step, the script will change the governance address to Badger's Governance Multisig;
    this will effectively relinquish the contract control from your account to the Badger Governance.
    Additionally, the script performs a final check of all parameters against the registry parameters.
    """

    # Get deployer account from local keystore
    dev = connect_account()

    # Add deployed Strategy and Vault contracts here:
    STRAT = DEPLOYED_STRAT_ADDR
    VAULT = DEPLOYED_VAULT_ADDR

    assert STRAT != "123"
    assert VAULT != "123"
    
    strategy = StrategybveOxdOxdStakingOptimizer.at(STRAT)
    vault = TheVault.at(VAULT)

    assert strategy.paused() == False
    assert vault.paused() == False

    console.print("[blue]Strategy: [/blue]", strategy.getName())
    console.print("[blue]Vault: [/blue]", vault.name())

    # Get production addresses from registry
    registry = interface.IBadgerRegistry(REGISTRY)

    governance = registry.get("governance")
    guardian = registry.get("guardian")
    keeper = registry.get("keeper")
    badger_tree = registry.get("badgerTree")

    assert governance != AddressZero
    assert guardian != AddressZero
    assert keeper != AddressZero
    assert badger_tree != AddressZero

    # Check production parameters and update any mismatch
    set_parameters(
        dev,
        strategy,
        vault,
        governance,
        guardian,
        keeper,
    )

    # Confirm all productions parameters
    check_parameters(
        strategy, vault, governance, guardian, keeper, badger_tree
    )


def set_parameters(dev, strategy, vault, governance, guardian, keeper):

    # Set Fees
    if vault.performanceFeeGovernance() != 0:
        vault.setPerformanceFeeGovernance(0, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.performanceFeeStrategist() != 0:
        vault.setPerformanceFeeStrategist(0, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.withdrawalFee() != 10:
        vault.setWithdrawalFee(10, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.managementFee() != 0:
        vault.setPerformanceFeeGovernance(0, {"from": dev})
        time.sleep(sleep_between_tx)

    console.print("[green]Fees existing or set at: [/green]", "0, 0, 10")

    # Set permissioned accounts
    if strategy.keeper() != keeper:
        strategy.setKeeper(keeper, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.keeper() != keeper:
        vault.setKeeper(keeper, {"from": dev})
        time.sleep(sleep_between_tx)

    console.print("[green]Keeper existing or set at: [/green]", keeper)

    if strategy.guardian() != guardian:
        strategy.setGuardian(guardian, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.guardian() != guardian:
        vault.setGuardian(guardian, {"from": dev})
        time.sleep(sleep_between_tx)

    console.print("[green]Guardian existing or set at: [/green]", guardian)

    if strategy.strategist() != governance:
        strategy.setStrategist(governance, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.strategist() != governance:
        vault.setStrategist(governance, {"from": dev})
        time.sleep(sleep_between_tx)

    console.print("[green]Strategist existing or set at: [/green]", governance)

    if vault.strategy() != strategy.address:
        vault.setStrategy(strategy.address, {"from": dev})
        time.sleep(sleep_between_tx)

    console.print("[green]Vault strategy existing or set at: [/green]", strategy.address)

    if strategy.governance() != governance:
        strategy.setGovernance(governance, {"from": dev})
        time.sleep(sleep_between_tx)
    if vault.governance() != governance:
        vault.setGovernance(governance, {"from": dev})
        time.sleep(sleep_between_tx)

    console.print("[green]Governance existing or set at: [/green]", governance)


def check_parameters(
    strategy, vault, governance, guardian, keeper, badger_tree
):
    assert strategy.want() == WANT
    assert vault.token() == WANT

    assert vault.managementFee() == 0
    assert vault.performanceFeeGovernance() == 0
    assert vault.performanceFeeStrategist() == 0
    assert vault.withdrawalFee() == 10

    assert strategy.keeper() == keeper
    assert vault.keeper() == keeper
    assert strategy.guardian() == guardian
    assert vault.guardian() == guardian
    assert strategy.strategist() == governance
    assert vault.strategist() == governance
    assert strategy.governance() == governance
    assert vault.governance() == governance

    # Not all strategies use the badger_tree
    try:
        if strategy.badgerTree() != AddressZero:
            assert strategy.badgerTree() == badger_tree
    except:
        pass

    console.print("[blue]All Parameters checked![/blue]")


def connect_account():
    click.echo(f"You are using the '{network.show_active()}' network")
    dev = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))
    click.echo(f"You are using: 'dev' [{dev.address}]")
    return dev

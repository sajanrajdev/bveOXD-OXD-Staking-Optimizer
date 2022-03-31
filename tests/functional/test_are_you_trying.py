from brownie import *
from helpers.constants import MaxUint256, AddressZero


def test_are_you_trying(deployer, vault, strategy, want, governance):
    """
    Verifies that you set up the Strategy properly
    """
    # Setup
    startingBalance = want.balanceOf(deployer)

    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    assert startingBalance >= 0
    # End Setup

    # Deposit
    assert want.balanceOf(vault) == 0

    want.approve(vault, MaxUint256, {"from": deployer})
    vault.deposit(depositAmount, {"from": deployer})

    available = vault.available()
    assert available > 0

    # Confirm that userProxy hasn't been generated
    assert strategy.getUserProxy() == AddressZero

    # Balance of pool is zero before staking
    assert strategy.balanceOfPool() == 0

    vault.earn({"from": governance})

    # Confirm that userProxy has been generated after first deposit
    assert strategy.getUserProxy() != AddressZero

    chain.sleep(100000 * 13)  # Mine so we get some interest
    chain.mine(1)  # Mine so we get some interest

    ## TEST 1: Does the want get used in any way?
    assert want.balanceOf(vault) == depositAmount - available

    # Did the strategy do something with the asset?
    assert want.balanceOf(strategy) < available

    # Confirm that the balance of the Pool increased
    assert strategy.balanceOfPool() > 0

    # Use this if it should invest all
    assert want.balanceOf(strategy) == 0

    # Check that rewards have been earned
    # stakingContract = interface.IMultiRewards(strategy.stakingAddress())
    print("Ratio:", strategy.getSolidlyPoolRatio(strategy.OXD(), strategy.BVEOXD(), False))
    print("Earned:", strategy.balanceOfRewards())

    ## TEST 2: Is the Harvest profitable?
    harvest = strategy.harvest({"from": governance})
    event = harvest.events["Harvested"]
    # If it doesn't print, we don't want it
    assert event["token"] == want
    assert event["amount"] >= 0

    ## TEST 3: Does the strategy emit anything?
    event = harvest.events["TreeDistribution"]
    assert event["token"] == strategy.bOxSolid()
    assert event["amount"] > 0
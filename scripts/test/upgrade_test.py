from brownie import accounts, interface, StrategybveOxdOxdStakingOptimizer
from rich.console import Console
from brownie.test.managers.runner import RevertContextManager as reverts

C = Console()

STRAT_ADDRESS = "0x00B154A7fBF57a09DeeC960f152205d5aE9795AE"
DEV_PROXY = "0x20Dce41Acca85E8222D6861Aa6D23B6C941777bF"
DEV_MULTI = "0x4c56ee3295042f8A5dfC83e770a21c707CB46f5b"

def main():
    gov = accounts.at(DEV_MULTI, force=True)
    strat = StrategybveOxdOxdStakingOptimizer.at(STRAT_ADDRESS, owner=gov)

    # Record current balances (Balance of rewards varies slightly from block to block)
    balanceOf = strat.balanceOf()
    balanceOfPool = strat.balanceOfPool()
    balanceOfWant = strat.balanceOfWant()

    # Storage variables
    governance = strat.governance()
    guardian = strat.guardian()
    keeper = strat.keeper()
    strategist = strat.strategist()
    sl = strat.sl()
    stakingAddress = strat.stakingAddress()
    userProxyInterface = strat.userProxyInterface()
    want = strat.want()
    vault = strat.vault()
    oxLens = strat.oxLens()
    bveOXD = strat.bveOXD()
    bOxSolid = strat.bOxSolid()

    # Test failing harvest
    with reverts("BaseV1Router: INSUFFICIENT_B_AMOUNT"):
        strat.harvest({"from": gov})

    # Execute upgrade
    logic = StrategybveOxdOxdStakingOptimizer.deploy({"from": gov})
    proxyAdmin = interface.IProxyAdmin(DEV_PROXY, owner=gov)
    proxyAdmin.upgrade(strat.address, logic.address)

    # Check balances
    assert balanceOf == strat.balanceOf()
    assert balanceOfPool == strat.balanceOfPool()
    assert balanceOfWant == strat.balanceOfWant()

    # Check storage
    assert governance == strat.governance()
    assert guardian == strat.guardian()
    assert keeper == strat.keeper()
    assert strategist == strat.strategist()
    assert sl == strat.sl()
    assert stakingAddress == strat.stakingAddress()
    assert userProxyInterface == strat.userProxyInterface()
    assert want == strat.want()
    assert vault == strat.vault()
    assert oxLens == strat.oxLens()
    assert bveOXD == strat.bveOXD()
    assert bOxSolid == strat.bOxSolid()

    # Test harvest
    tx = strat.harvest({"from": gov})
    print(tx.return_value)
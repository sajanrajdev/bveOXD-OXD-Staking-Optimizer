from helpers.StrategyCoreResolver import StrategyCoreResolver
from rich.console import Console
from brownie import interface
from _setup.config import WANT

console = Console()


class StrategyResolver(StrategyCoreResolver):
    def get_strategy_destinations(self):
        """
        Track balances for all strategy implementations
        (Strategy Must Implement)
        """
        strategy = self.manager.strategy
        sett = self.manager.sett
        return {
            "StakingRewards": strategy.stakingAddress(),
            "bveOXD": strategy.bveOXD(),
            "bveOXD_OXD_LP": strategy.want(),
            "bOxSolid": strategy.bOxSolid(),
            "badgerTree": sett.badgerTree(),
        }

    def add_balances_snap(self, calls, entities):
        super().add_balances_snap(calls, entities)
        strategy = self.manager.strategy

        oxd = interface.IERC20(strategy.OXD())
        oxSolid = interface.IERC20(strategy.OXSOLID())
        solid = interface.IERC20(strategy.SOLID())
        bveOXD = interface.IERC20(strategy.bveOXD())
        bOxSolid = interface.IERC20(strategy.bOxSolid())

        calls = self.add_entity_balances_for_tokens(calls, "oxd", oxd, entities)
        calls = self.add_entity_balances_for_tokens(calls, "oxSolid", oxSolid, entities)
        calls = self.add_entity_balances_for_tokens(calls, "solid", solid, entities)
        calls = self.add_entity_balances_for_tokens(calls, "bveOXD", bveOXD, entities)
        calls = self.add_entity_balances_for_tokens(calls, "bOxSolid", bOxSolid, entities)

        return calls

    def confirm_harvest(self, before, after, tx):
        console.print("=== Compare Harvest ===")
        self.manager.printCompare(before, after)
        self.confirm_harvest_state(before, after, tx)

        super().confirm_harvest(before, after, tx)

        assert len(tx.events["Harvested"]) == 1
        event = tx.events["Harvested"][0]

        assert event["token"] == WANT
        assert event["amount"] == after.get("sett.balance") - before.get("sett.balance")

        assert len(tx.events["TreeDistribution"]) == 1
        event = tx.events["TreeDistribution"][0]

        assert after.balances("bOxSolid", "badgerTree") > before.balances(
            "bOxSolid", "badgerTree"
        )

        if before.get("sett.performanceFeeGovernance") > 0:
            assert after.balances("bOxSolid", "treasury") > before.balances(
                "bOxSolid", "treasury"
            )

        if before.get("sett.performanceFeeStrategist") > 0:
            assert after.balances("bOxSolid", "strategist") > before.balances(
                "bOxSolid", "strategist"
            )

        assert event["token"] == self.manager.strategy.bBveOxd_Oxd()
        assert event["amount"] == after.balances(
            "bOxSolid", "badgerTree"
        ) - before.balances("bOxSolid", "badgerTree")

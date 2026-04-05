from __future__ import annotations

from .models import ControlAction, EnergySnapshot, ForecastBundle, OptimizationResult, PriceBundle


class DeyeStrategyPlanner:
    """Economic planner focused on Deye/Sunsynk-style controls.

    This is still heuristic, but it already combines tomorrow PV surplus,
    overnight demand, import/export prices and a simple battery cycle cost.
    """

    def plan(
        self,
        snapshot: EnergySnapshot,
        forecast: ForecastBundle,
        prices: PriceBundle,
        *,
        min_soc: float,
        max_soc: float,
        export_allowed: bool,
        grid_charge_allowed: bool,
        battery_cycle_cost: float,
    ) -> OptimizationResult:
        battery_energy_kwh = snapshot.battery_capacity_kwh * snapshot.battery_soc / 100
        min_energy_kwh = snapshot.battery_capacity_kwh * min_soc / 100
        max_energy_kwh = snapshot.battery_capacity_kwh * max_soc / 100
        storage_headroom_kwh = max(max_energy_kwh - battery_energy_kwh, 0.0)
        expected_surplus_kwh = max(forecast.solar_kwh_next_24h - forecast.load_kwh_next_24h, 0.0)

        future_self_consumption_value = max(prices.avg_import_price - battery_cycle_cost, 0.0)
        export_value_now = max(prices.highest_export_price - battery_cycle_cost, 0.0)
        cheap_import_now = prices.cheapest_import_price > 0 and prices.cheapest_import_price < future_self_consumption_value * 0.7
        high_export_window = export_allowed and export_value_now > future_self_consumption_value * 1.1
        high_solar_tomorrow = expected_surplus_kwh > storage_headroom_kwh * 0.75
        low_solar_tomorrow = forecast.solar_kwh_next_24h < max(forecast.load_kwh_overnight * 0.8, 2.0)

        target_morning_soc = max_soc
        should_discharge_overnight = False
        should_export_overnight = False
        actions: list[ControlAction] = []
        summary_parts: list[str] = []

        if high_solar_tomorrow:
            target_morning_soc = min_soc
            should_discharge_overnight = True
            should_export_overnight = high_export_window
            actions.append(
                ControlAction(
                    action="deye_set_target_morning_soc",
                    value=round(target_morning_soc, 1),
                    reason="Tomorrow PV surplus is expected to exceed remaining battery headroom.",
                )
            )
            actions.append(
                ControlAction(
                    action="deye_set_load_limit_mode",
                    value="Allow Export" if should_export_overnight else "Essentials",
                    reason="Night behaviour selected based on forecast surplus and export economics.",
                )
            )
            actions.append(
                ControlAction(
                    action="deye_set_battery_charge_current",
                    value=1 if should_export_overnight else 5,
                    reason="Low charge current leaves room for early high-value export or next-morning PV capture.",
                )
            )
            summary_parts.append(f"tomorrow surplus {expected_surplus_kwh:.1f} kWh")
            if should_export_overnight:
                actions.append(
                    ControlAction(
                        action="deye_allow_export_discharge",
                        value=True,
                        reason="Export value is currently better than storing the energy for expected self-consumption.",
                    )
                )
                summary_parts.append("night export enabled")
            else:
                summary_parts.append("night discharge limited to house load")

        elif low_solar_tomorrow and grid_charge_allowed and cheap_import_now:
            target_morning_soc = max(min_soc + 35, min(max_soc, 55))
            actions.append(
                ControlAction(
                    action="deye_force_grid_charge",
                    value=True,
                    reason="Low PV forecast tomorrow and current import prices are cheap relative to expected later consumption.",
                )
            )
            actions.append(
                ControlAction(
                    action="deye_set_target_morning_soc",
                    value=round(target_morning_soc, 1),
                    reason="Prepare stored energy for a weak-solar day.",
                )
            )
            actions.append(
                ControlAction(
                    action="deye_set_program_1_mode",
                    value="Charge",
                    reason="Use Deye TOU program slot to allow overnight charging from grid.",
                )
            )
            summary_parts.append("overnight grid charge planned")

        else:
            target_morning_soc = max(min_soc, min(snapshot.battery_soc, max_soc))
            actions.append(
                ControlAction(
                    action="deye_hold_strategy",
                    value=round(target_morning_soc, 1),
                    reason="No strong economic or forecast signal justifies aggressive battery action.",
                )
            )
            actions.append(
                ControlAction(
                    action="deye_set_load_limit_mode",
                    value="Zero Export" if export_allowed else "Essentials",
                    reason="Default safe mode while holding the current energy strategy.",
                )
            )
            summary_parts.append("hold strategy")

        if forecast.solar_kwh_next_24h > forecast.load_kwh_next_24h and export_allowed:
            actions.append(
                ControlAction(
                    action="deye_limit_early_pv_battery_charging",
                    value=True,
                    reason="If morning export value is high, battery charging can be temporarily limited to monetize surplus first.",
                )
            )

        summary = (
            f"Deye plan: {', '.join(summary_parts)}. "
            f"Avg import {prices.avg_import_price:.3f}, max export {prices.highest_export_price:.3f}."
        )

        return OptimizationResult(
            target_morning_soc=target_morning_soc,
            expected_surplus_kwh=expected_surplus_kwh,
            should_discharge_overnight=should_discharge_overnight,
            should_export_overnight=should_export_overnight,
            summary=summary,
            actions=actions,
        )

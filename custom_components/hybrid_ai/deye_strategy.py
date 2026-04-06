from __future__ import annotations

from homeassistant.util import dt as dt_util

from .models import (
    ControlAction,
    EnergySnapshot,
    ForecastBundle,
    HourPlan,
    OptimizationResult,
    PriceBundle,
    TouPeriod,
)


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
        hourly_load: list[dict],
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
        hourly_schedule = self._build_hourly_schedule(
            forecast,
            prices,
            hourly_load,
            export_allowed=export_allowed,
            grid_charge_allowed=grid_charge_allowed,
            battery_cycle_cost=battery_cycle_cost,
        )
        tou_periods = self._build_tou_periods(hourly_schedule)
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
        if tou_periods:
            actions.append(
                ControlAction(
                    action="deye_apply_tou_schedule",
                    value=[
                        {
                            "program": period.program,
                            "start_hour": period.start_hour,
                            "end_hour": period.end_hour,
                            "mode": period.mode,
                            "label": period.label,
                        }
                        for period in tou_periods
                    ],
                    reason="Apply compressed hourly schedule to available Deye TOU program slots.",
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
            hourly_schedule=hourly_schedule,
            tou_periods=tou_periods,
        )

    def _build_hourly_schedule(
        self,
        forecast: ForecastBundle,
        prices: PriceBundle,
        hourly_load: list[dict],
        *,
        export_allowed: bool,
        grid_charge_allowed: bool,
        battery_cycle_cost: float,
    ) -> list[HourPlan]:
        avg_hourly_pv = forecast.solar_kwh_next_24h / 24 if forecast.solar_kwh_next_24h else 0.0
        import_prices = prices.import_prices[:24] if prices.import_prices else []
        export_prices = prices.export_prices[:24] if prices.export_prices else []
        highest_export = prices.highest_export_price
        cheapest_import = prices.cheapest_import_price
        avg_import = prices.avg_import_price

        schedule: list[HourPlan] = []
        for hour_offset, slot in enumerate(hourly_load):
            slot_start = slot["start"].replace(minute=0, second=0, microsecond=0)
            load_kwh = slot["load_w"] / 1000
            import_price = import_prices[hour_offset] if hour_offset < len(import_prices) else prices.avg_import_price
            export_price = export_prices[hour_offset] if hour_offset < len(export_prices) else prices.avg_export_price

            if 10 <= slot_start.hour <= 15:
                pv_kwh = avg_hourly_pv * 1.9
            elif 7 <= slot_start.hour < 10 or 16 <= slot_start.hour <= 18:
                pv_kwh = avg_hourly_pv * 0.9
            else:
                pv_kwh = avg_hourly_pv * 0.15

            if pv_kwh > load_kwh * 1.25 and export_allowed and export_price >= max(highest_export * 0.85, avg_import - battery_cycle_cost):
                mode = "export_surplus"
                notes = "High PV and strong export value."
            elif slot_start.hour < 6 and grid_charge_allowed and import_price > 0 and import_price <= max(cheapest_import * 1.1, avg_import * 0.7):
                mode = "grid_charge"
                notes = "Cheap import window."
            elif slot_start.hour < 8 and forecast.solar_kwh_next_24h > forecast.load_kwh_next_24h:
                mode = "preserve_headroom"
                notes = "Hold battery headroom before solar ramp."
            elif slot_start.hour >= 18 and export_allowed and export_price >= avg_import:
                mode = "export_battery"
                notes = "Evening export window."
            else:
                mode = "self_use"
                notes = "Default self-consumption mode."

            schedule.append(
                HourPlan(
                    start=slot_start,
                    mode=mode,
                    expected_load_kwh=round(load_kwh, 3),
                    expected_pv_kwh=round(max(pv_kwh, 0.0), 3),
                    import_price=round(import_price, 4),
                    export_price=round(export_price, 4),
                    notes=notes,
                )
            )
        return schedule

    def _build_tou_periods(self, hourly_schedule: list[HourPlan]) -> list[TouPeriod]:
        active_modes = {"grid_charge", "export_battery", "export_surplus"}
        grouped: list[tuple[int, int, str]] = []

        index = 0
        while index < len(hourly_schedule):
            slot = hourly_schedule[index]
            if slot.mode not in active_modes:
                index += 1
                continue

            start_hour = slot.start.hour
            mode = slot.mode
            end_hour = start_hour + 1
            cursor = index + 1
            while cursor < len(hourly_schedule):
                next_slot = hourly_schedule[cursor]
                if next_slot.mode != mode or next_slot.start.hour != end_hour:
                    break
                end_hour += 1
                cursor += 1

            grouped.append((start_hour, end_hour, mode))
            index = cursor

        grouped.sort(key=lambda item: (self._mode_priority(item[2]), -(item[1] - item[0]), item[0]))
        selected = grouped[:3]

        periods: list[TouPeriod] = []
        for program_index, (start_hour, end_hour, mode) in enumerate(selected, start=1):
            periods.append(
                TouPeriod(
                    program=program_index,
                    start_hour=start_hour,
                    end_hour=min(end_hour, 24),
                    mode=mode,
                    label=mode.replace("_", " "),
                )
            )
        return periods

    def _mode_priority(self, mode: str) -> int:
        priorities = {
            "grid_charge": 0,
            "export_battery": 1,
            "export_surplus": 2,
        }
        return priorities.get(mode, 9)

from __future__ import annotations

from .models import ControlAction, EnergySnapshot, ForecastBundle, OptimizationResult


class BatteryOptimizer:
    def optimize(
        self,
        snapshot: EnergySnapshot,
        forecast: ForecastBundle,
        *,
        min_soc: float,
        max_soc: float,
        export_allowed: bool,
    ) -> OptimizationResult:
        usable_kwh = snapshot.battery_capacity_kwh * max((max_soc - min_soc) / 100, 0)
        current_energy_kwh = snapshot.battery_capacity_kwh * snapshot.battery_soc / 100
        min_energy_kwh = snapshot.battery_capacity_kwh * min_soc / 100

        expected_surplus_kwh = max(forecast.solar_kwh_next_24h - forecast.load_kwh_next_24h, 0.0)
        storage_headroom_kwh = max((snapshot.battery_capacity_kwh * max_soc / 100) - current_energy_kwh, 0.0)

        target_morning_soc = max_soc
        should_discharge_overnight = False
        should_export_overnight = False
        actions: list[ControlAction] = []

        if expected_surplus_kwh > storage_headroom_kwh * 0.75:
            target_morning_soc = min_soc
            should_discharge_overnight = True
            should_export_overnight = export_allowed
        elif expected_surplus_kwh > usable_kwh * 0.35:
            target_morning_soc = min(min_soc + 10, max_soc)
            should_discharge_overnight = True

        target_morning_soc = max(min_soc, min(target_morning_soc, max_soc))

        if should_discharge_overnight:
            actions.append(
                ControlAction(
                    action="set_target_morning_soc",
                    value=round(target_morning_soc, 1),
                    reason="Forecast surplus is higher than remaining storage headroom.",
                )
            )
            actions.append(
                ControlAction(
                    action="allow_overnight_discharge",
                    value=True,
                    reason=f"Make room for roughly {expected_surplus_kwh:.1f} kWh of forecast surplus.",
                )
            )
            if should_export_overnight:
                actions.append(
                    ControlAction(
                        action="allow_export_discharge",
                        value=True,
                        reason="Export is allowed and forecast indicates a high solar day tomorrow.",
                    )
                )
            summary = (
                f"Reduce battery overnight toward {target_morning_soc:.0f}% SOC. "
                f"Forecast surplus: {expected_surplus_kwh:.1f} kWh."
            )
        else:
            actions.append(
                ControlAction(
                    action="hold_reserve",
                    value=round(max(snapshot.battery_soc, min_soc), 1),
                    reason="Forecast does not justify proactive overnight discharge.",
                )
            )
            summary = (
                f"Keep reserve. Forecast surplus {expected_surplus_kwh:.1f} kWh does not justify aggressive discharge."
            )

        return OptimizationResult(
            target_morning_soc=target_morning_soc,
            expected_surplus_kwh=expected_surplus_kwh,
            should_discharge_overnight=should_discharge_overnight,
            should_export_overnight=should_export_overnight,
            summary=summary,
            actions=actions,
        )

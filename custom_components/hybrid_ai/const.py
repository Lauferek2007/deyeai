DOMAIN = "hybrid_ai"

CONF_ADAPTER = "adapter"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_BATTERY_CAPACITY_KWH = "battery_capacity_kwh"
CONF_LOAD_POWER_ENTITY = "load_power_entity"
CONF_PV_POWER_ENTITY = "pv_power_entity"
CONF_GRID_POWER_ENTITY = "grid_power_entity"
CONF_SOLAR_FORECAST_ENTITY = "solar_forecast_entity"
CONF_MIN_SOC = "min_soc"
CONF_MAX_SOC = "max_soc"
CONF_ENABLE_WRITE_MODE = "enable_write_mode"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"
CONF_EXPORT_ALLOWED = "export_allowed"

DEFAULT_NAME = "Hybrid AI Energy Manager"
DEFAULT_MIN_SOC = 15
DEFAULT_MAX_SOC = 95
DEFAULT_UPDATE_INTERVAL_MINUTES = 15

ATTR_PLAN_SUMMARY = "plan_summary"
ATTR_FORECAST_SOLAR_KWH = "forecast_solar_kwh"
ATTR_FORECAST_LOAD_KWH = "forecast_load_kwh"
ATTR_EXPECTED_SURPLUS_KWH = "expected_surplus_kwh"
ATTR_TARGET_MORNING_SOC = "target_morning_soc"
ATTR_ADAPTER_ACTIONS = "adapter_actions"

SERVICE_RUN_OPTIMIZATION = "run_optimization"

DOMAIN = "hybrid_ai"

CONF_ADAPTER = "adapter"
CONF_AUTO_DISCOVERY = "auto_discovery"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_BATTERY_CAPACITY_KWH = "battery_capacity_kwh"
CONF_LOAD_POWER_ENTITY = "load_power_entity"
CONF_PV_POWER_ENTITY = "pv_power_entity"
CONF_GRID_POWER_ENTITY = "grid_power_entity"
CONF_SOLAR_FORECAST_ENTITY = "solar_forecast_entity"
CONF_PRICE_IMPORT_ENTITY = "price_import_entity"
CONF_PRICE_EXPORT_ENTITY = "price_export_entity"
CONF_WEEKLY_LOAD_OFFSETS = "weekly_load_offsets"
CONF_DEYE_LOAD_LIMIT_ENTITY = "deye_load_limit_entity"
CONF_DEYE_BATTERY_MAX_CHARGE_CURRENT_ENTITY = "deye_battery_max_charge_current_entity"
CONF_DEYE_PROGRAM_1_MODE_ENTITY = "deye_program_1_mode_entity"
CONF_MIN_SOC = "min_soc"
CONF_MAX_SOC = "max_soc"
CONF_ENABLE_WRITE_MODE = "enable_write_mode"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"
CONF_EXPORT_ALLOWED = "export_allowed"
CONF_GRID_CHARGE_ALLOWED = "grid_charge_allowed"
CONF_BATTERY_CYCLE_COST = "battery_cycle_cost"

DEFAULT_NAME = "Hybrid AI Energy Manager"
DEFAULT_ADAPTER = "auto"
DEFAULT_MIN_SOC = 15
DEFAULT_MAX_SOC = 95
DEFAULT_UPDATE_INTERVAL_MINUTES = 15
DEFAULT_BATTERY_CYCLE_COST = 0.05

ATTR_PLAN_SUMMARY = "plan_summary"
ATTR_FORECAST_SOLAR_KWH = "forecast_solar_kwh"
ATTR_FORECAST_LOAD_KWH = "forecast_load_kwh"
ATTR_EXPECTED_SURPLUS_KWH = "expected_surplus_kwh"
ATTR_TARGET_MORNING_SOC = "target_morning_soc"
ATTR_ADAPTER_ACTIONS = "adapter_actions"
ATTR_DISCOVERY = "discovery"
ATTR_PRICE_CONTEXT = "price_context"
ATTR_LOAD_PROFILE = "load_profile"
ATTR_HOURLY_SCHEDULE = "hourly_schedule"

DEFAULT_WEEKLY_LOAD_OFFSETS = []

SERVICE_RUN_OPTIMIZATION = "run_optimization"
SERVICE_DISCOVER_ENTITIES = "discover_entities"

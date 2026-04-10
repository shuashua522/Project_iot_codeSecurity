def is_brightness_below_10() -> bool:
    LIGHT_ENTITY_ID = "light.philips_cn_1061200910_lite_s_2"
    try:
        light_data = tool_get_states_by_entity_id({"entity_id": LIGHT_ENTITY_ID})
        brightness = int(light_data["attributes"].get("brightness", 0))
        return brightness <= 25
    except Exception:
        return False
def _external_connection_disabled(*args, **kwargs):
    raise RuntimeError("External connections are disabled by policy and cannot be performed.")
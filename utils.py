def list_to_comma_string(items):
    if items is None:
        return ""
    if isinstance(items, list):
        return ",".join([str(i).strip() for i in items if str(i).strip()])
    return str(items)

def comma_string_to_list(s: str):
    if not s:
        return []
    return [p.strip() for p in s.split(",") if p.strip()]

"""subarea_run.yml loader + validation (frozen schema v1, FR-19 v2 design doc §3)."""
import os
import yaml

REQUIRED_TOP = ["project", "network", "subarea", "time", "assignment",
                "demand_classes", "trajectory_export", "output_folder"]


class ConfigError(ValueError):
    pass


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    missing = [k for k in REQUIRED_TOP if k not in cfg]
    if missing:
        raise ConfigError(f"subarea_run.yml missing sections: {missing}")

    net = cfg["network"]
    for f_ in ("node.csv", "link.csv"):
        p = os.path.join(net["gmns_folder"], f_)
        if not os.path.exists(p):
            raise ConfigError(f"network file not found: {p}")
    if net.get("link_id_space") not in ("original", "internal"):
        raise ConfigError("network.link_id_space must be 'original' or 'internal'")

    sa = cfg["subarea"]
    if not sa.get("focus_link_file") and not sa.get("focus_rule"):
        raise ConfigError("subarea needs focus_link_file or focus_rule")

    wsl = cfg["time"].get("warm_start_link_performance")
    if wsl and not os.path.exists(wsl):
        raise ConfigError(f"warm_start_link_performance not found: {wsl}")

    os.makedirs(cfg["output_folder"], exist_ok=True)
    return cfg

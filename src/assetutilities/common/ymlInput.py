from collections.abc import Mapping

import yaml


def ymlInput(defaultYml, updateYml):
    with open(defaultYml) as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    if updateYml is not None:
        #  Update values file
        try:
            with open(updateYml) as ymlfile:
                cfgUpdateValues = yaml.safe_load(ymlfile)
            #  Convert to logs
            # print(cfgUpdateValues)
            cfg = update_deep(cfg, cfgUpdateValues)
        except Exception as e:
            # Surface the cause; this handler previously discarded it entirely
            # (issue #80). Fallback behaviour is unchanged.
            print(
                "Update Input file could not be loaded successfully. Running program default values"
            )
            print(f"Error is : {e}")

    return cfg


def update_deep(d, u):
    for k, v in u.items():
        # this condition handles the problem
        if not isinstance(d, Mapping):
            d = u
        elif isinstance(v, Mapping):
            r = update_deep(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]

    return d

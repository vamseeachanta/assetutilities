# ABOUTME: Engineering-value regression checks for ResultEnvelope serialization.
"""Preserve computed gauge pressure through the workflow result contract.

Source: OpenStax, University Physics Volume 1 (2016), section 14.1,
"Pressure at a Depth for a Fluid of Constant Density", equation 14.4:
p = p_surface + rho*g*h, hence gauge pressure = rho*g*h.
https://openstax.org/books/university-physics-volume-1/pages/14-1-fluids-density-and-pressure

Density and gravity below are synthetic prescribed inputs, not fluid-property
defaults or a claim about local gravity. Only constant-density static pressure
is represented; no design acceptance limit is applied.
"""

import json

import pytest

from assetutilities.workflow_api.envelope import ResultEnvelope


@pytest.mark.parametrize("transport", ["dict", "json"])
@pytest.mark.parametrize(
    ("depth_m", "expected_pressure_pa"),
    [
        pytest.param(0.0, 0.0, id="surface"),
        pytest.param(2.0, 19441.5, id="submerged"),
        pytest.param(1.25, 12150.9375, id="fractional-pressure"),
    ],
)
def test_gauge_pressure_survives_envelope_roundtrip(
    transport, depth_m, expected_pressure_pa
):
    """Hand references using OpenStax (2016), section 14.1, equation 14.4.

    Prescribed rho = 997 kg/m^3 and g = 9.75 m/s^2 give rho*g = 9720.75:
    - h = 0 m:    9720.75 * 0    =     0 Pa (surface gauge pressure).
    - h = 2 m:    9720.75 * 2    = 19441.5 Pa.
    - h = 1.25 m: 9720.75 * 5/4  = 12150.9375 Pa.

    The expected values in the table are independent hand calculations, not
    values recovered from the envelope. All operands and products are exactly
    representable as binary floats, so equality needs no numerical tolerance.
    """
    # Synthetic inputs for equation 14.4, cited above; no material constants.
    density_kg_m3 = 997.0
    gravity_m_s2 = 9.75
    computed_pressure_pa = density_kg_m3 * gravity_m_s2 * depth_m
    envelope = ResultEnvelope(
        workflow_id="synthetic_hydrostatic_pressure",
        status="ok",
        result={
            "kind": "in_memory",
            "value": {"gauge_pressure": computed_pressure_pa, "unit": "Pa"},
        },
        provenance={},
        determinism={},
    )

    serialized = envelope.to_dict()
    if transport == "json":
        serialized = json.loads(json.dumps(serialized, allow_nan=False))
    restored = ResultEnvelope.from_dict(serialized)

    assert restored.status == "ok"
    assert restored.result["kind"] == "in_memory"
    pressure = restored.result["value"]
    assert isinstance(pressure["gauge_pressure"], float)
    assert pressure["gauge_pressure"] == expected_pressure_pa
    assert pressure["unit"] == "Pa"

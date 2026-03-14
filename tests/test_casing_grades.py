# ABOUTME: Tests for API 5CT casing grades and pipe geometry helpers.
# ABOUTME: Validates grade properties and cross-section geometry calculations.
import pytest
import math


class TestAPI5CTGrades:
    def test_j55_exists(self):
        from assetutilities.constants.casing_grades import CASING_GRADES
        assert "J55" in CASING_GRADES
        assert CASING_GRADES["J55"].smys_mpa == 379
        assert CASING_GRADES["J55"].suts_mpa == 517

    def test_n80_exists(self):
        from assetutilities.constants.casing_grades import CASING_GRADES
        assert "N80" in CASING_GRADES
        assert CASING_GRADES["N80"].smys_mpa == 552

    def test_p110_exists(self):
        from assetutilities.constants.casing_grades import CASING_GRADES
        assert "P110" in CASING_GRADES
        assert CASING_GRADES["P110"].smys_mpa == 758

    def test_l80_exists(self):
        from assetutilities.constants.casing_grades import CASING_GRADES
        assert "L80" in CASING_GRADES

    def test_q125_exists(self):
        from assetutilities.constants.casing_grades import CASING_GRADES
        assert "Q125" in CASING_GRADES
        assert CASING_GRADES["Q125"].smys_mpa == 862


class TestPipeGeometry:
    def test_cross_section_area(self):
        from assetutilities.math_helpers import pipe_cross_section_area
        # 12.75" OD, 0.5" WT
        od_m = 12.75 * 0.0254  # convert inches to meters
        wt_m = 0.5 * 0.0254
        area = pipe_cross_section_area(od_m, wt_m)
        # A = pi/4 * (OD^2 - ID^2)
        id_m = od_m - 2 * wt_m
        expected = math.pi / 4 * (od_m**2 - id_m**2)
        assert abs(area - expected) < 1e-8

    def test_moment_of_inertia(self):
        from assetutilities.math_helpers import pipe_moment_of_inertia
        od_m = 0.3239  # 12.75"
        wt_m = 0.0127  # 0.5"
        I = pipe_moment_of_inertia(od_m, wt_m)
        assert I > 0

    def test_section_modulus(self):
        from assetutilities.math_helpers import pipe_section_modulus
        od_m = 0.3239
        wt_m = 0.0127
        Z = pipe_section_modulus(od_m, wt_m)
        # Z = I / (OD/2)
        from assetutilities.math_helpers import pipe_moment_of_inertia
        I = pipe_moment_of_inertia(od_m, wt_m)
        assert abs(Z - I / (od_m / 2)) < 1e-10

    def test_zero_wall_raises(self):
        from assetutilities.math_helpers import pipe_cross_section_area
        with pytest.raises(ValueError):
            pipe_cross_section_area(0.3, 0.0)

    def test_wall_exceeds_radius_raises(self):
        from assetutilities.math_helpers import pipe_cross_section_area
        with pytest.raises(ValueError):
            pipe_cross_section_area(0.3, 0.2)  # WT > OD/2

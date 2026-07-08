import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.checker import PolicyChecker
checker = PolicyChecker()

def test_ogl_cc_by_nc_violation():
    result = checker.check("air_quality", "ogl", "nhs_admissions", "cc_by_nc")
    assert result["compliant"] == False
    assert result["violation_type"] == "cc_by_nc_restriction"
    print("PASS: OGL + CC-BY-NC violation detected")

def test_ogl_ogl_compliant():
    result = checker.check("ons_census", "ogl", "police_crime", "ogl")
    assert result["compliant"] == True
    assert result["violation_type"] == None
    print("PASS: OGL + OGL is compliant")

def test_ogl_cc_by_sa_violation():
    result = checker.check("air_quality", "ogl", "met_office_weather", "cc_by_sa")
    assert result["compliant"] == False
    assert result["violation_type"] == "share_alike_conflict"
    print("PASS: OGL + CC-BY-SA violation detected")

def test_ogl_odbl_violation():
    result = checker.check("dft_traffic", "ogl", "osm_berkshire", "odbl")
    assert result["compliant"] == False
    assert result["violation_type"] == "odbl_restriction"
    print("PASS: OGL + ODbL violation detected")

def test_cc_by_nc_cc_by_sa_violation():
    result = checker.check("nhs_admissions", "cc_by_nc", "met_office_weather", "cc_by_sa")
    assert result["compliant"] == False
    assert result["violation_type"] == "nc_sa_conflict"
    print("PASS: CC-BY-NC + CC-BY-SA violation detected")

if __name__ == "__main__":
    print("=" * 50)
    print("RUNNING UNIT TESTS")
    print("=" * 50)
    test_ogl_cc_by_nc_violation()
    test_ogl_ogl_compliant()
    test_ogl_cc_by_sa_violation()
    test_ogl_odbl_violation()
    test_cc_by_nc_cc_by_sa_violation()
    print()
    print("ALL TESTS PASSED!")
    print("=" * 50)
import pytest
from scripts.check_quality import evaluate
from supportops_toolkit.evals import RegressionError


def test_p02_regression_gate_exercises_p05_and_rejects_degraded_fixture():
    assert evaluate().total==10
    with pytest.raises(RegressionError): evaluate(degraded=True)

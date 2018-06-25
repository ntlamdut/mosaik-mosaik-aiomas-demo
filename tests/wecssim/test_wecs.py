import numpy as np

from wecssim.wecs import WECS


def test_sim():
    wecs = WECS(
        P_rated=np.full(6, 10),
        v_rated=np.full(6, 10),
        v_min=np.full(6, 1),
        v_max=np.full(6, 15))
    print(wecs.P_rated)
    print(wecs.v_rated)
    print(wecs.v_min)
    print(wecs.v_max)

    # Test normal behavior
    wecs.step(np.array([0, 1, 5, 10, 15, 20]))
    assert np.allclose(wecs.P, [0, 0.01, 1.25, 10, 10, 0])

    # Test with P_max set:
    wecs.set_P_max(np.array([0, 0, 5, 5, 10, 10]))
    wecs.step(np.array([0, 10, 5, 10, 10, 10]))
    assert np.allclose(wecs.P, [0, 0, 1.25, 5, 10, 10])

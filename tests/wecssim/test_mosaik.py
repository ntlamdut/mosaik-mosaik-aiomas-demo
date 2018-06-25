import os.path

import pytest

from wecssim.mosaik import WecsSim


wind_data ="""5, 10
10, 10
"""


@pytest.fixture
def wind_file(tmpdir):
    wind_file = tmpdir.join('wind_data.csv')
    wind_file.write(wind_data)
    return wind_file.strpath


def test_wecssim(wind_file):
    wecssim = WecsSim()
    wecssim.init('wecssim-0', wind_file)

    assert not wecssim.wecs
    assert not wecssim.wecs_config

    ret = wecssim.create(2, 'WECS', P_rated=10, v_rated=10, v_min=1, v_max=15)
    assert ret == [
        {'eid': 'wecs-0', 'type': 'WECS'},
        {'eid': 'wecs-1', 'type': 'WECS'},
    ]

    ret = wecssim.create(1, 'WECS', P_rated=20, v_rated=10, v_min=1, v_max=15)
    assert ret == [
        {'eid': 'wecs-2', 'type': 'WECS'},
    ]

    assert len(wecssim.wecs) == 3
    assert len(wecssim.wecs_config) == 3

    wecssim.setup_done()

    ret = wecssim.step(0, {})
    assert ret == 900

    ret = wecssim.get_data({
        'wecs-0': ['P'],
        'wecs-1': ['P'],
        'wecs-2': ['P'],
    })

    assert ret == {
        'wecs-0': {'P': 1.25},
        'wecs-1': {'P': 10},
        'wecs-2': {'P': 2.5},
    }

    ret = wecssim.step(900, {
        'wecs-0': {},
        'wecs-1': {'P_max': {'src': 5}},
        'wecs-2': {'P_max': {'src': 12}},
    })
    assert ret == 1800

    ret = wecssim.get_data({
        'wecs-0': ['P'],
        'wecs-1': ['P'],
        'wecs-2': ['P'],
    })

    assert ret == {
        'wecs-0': {'P': 10},
        'wecs-1': {'P': 5},
        'wecs-2': {'P': 12},
    }

    pytest.raises(StopIteration, wecssim.step, 1800, {})

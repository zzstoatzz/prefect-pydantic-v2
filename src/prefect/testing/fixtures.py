import socket
from contextlib import contextmanager
from typing import Union

import anyio
import pendulum
import pytest
from websockets.legacy.server import WebSocketServer

from prefect.testing.utilities import AsyncMock


@pytest.fixture(autouse=True)
def add_prefect_loggers_to_caplog(caplog):
    import logging

    logger = logging.getLogger("prefect")
    logger.propagate = True

    try:
        yield
    finally:
        logger.propagate = False


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0



@pytest.fixture
def mock_anyio_sleep(monkeypatch):
    """
    Mock sleep used to not actually sleep but to set the current time to now + sleep
    delay seconds while still yielding to other tasks in the event loop.

    Provides "assert_sleeps_for" context manager which asserts a sleep time occurred
    within the context while using the actual runtime of the context as a tolerance.
    """
    original_now = pendulum.now
    original_sleep = anyio.sleep
    time_shift = 0.0

    async def callback(delay_in_seconds):
        nonlocal time_shift
        time_shift += float(delay_in_seconds)
        # Preserve yield effects of sleep
        await original_sleep(0)

    def latest_now(*args):
        # Fast-forwards the time by the total sleep time
        return original_now(*args).add(
            # Ensure we retain float precision
            seconds=int(time_shift),
            microseconds=(time_shift - int(time_shift)) * 1000000,
        )

    monkeypatch.setattr("pendulum.now", latest_now)

    sleep = AsyncMock(side_effect=callback)
    monkeypatch.setattr("anyio.sleep", sleep)

    @contextmanager
    def assert_sleeps_for(
        seconds: Union[int, float], extra_tolerance: Union[int, float] = 0
    ):
        """
        Assert that sleep was called for N seconds during the duration of the context.
        The runtime of the code during the context of the duration is used as an
        upper tolerance to account for sleeps that start based on a time. This is less
        brittle than attempting to freeze the current time.

        If an integer is provided, the upper tolerance will be rounded up to the nearest
        integer. If a float is provided, the upper tolerance will be a float.

        An optional extra tolerance may be provided to account for any other issues.
        This will be applied symmetrically.
        """
        run_t0 = original_now().timestamp()
        sleep_t0 = time_shift
        yield
        run_t1 = original_now().timestamp()
        sleep_t1 = time_shift
        runtime = run_t1 - run_t0
        if isinstance(seconds, int):
            # Round tolerance up to the nearest integer if input is an int
            runtime = int(runtime) + 1
        sleeptime = sleep_t1 - sleep_t0
        assert (
            sleeptime - float(extra_tolerance)
            <= seconds
            <= sleeptime + runtime + extra_tolerance
        ), (
            f"Sleep was called for {sleeptime}; expected {seconds} with tolerance of"
            f" +{runtime + extra_tolerance}, -{extra_tolerance}"
        )

    sleep.assert_sleeps_for = assert_sleeps_for

    return sleep




@pytest.fixture
def events_api_url(events_server: WebSocketServer, unused_tcp_port: int) -> str:
    return f"http://localhost:{unused_tcp_port}/accounts/A/workspaces/W"
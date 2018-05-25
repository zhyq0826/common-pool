import pytest
import pool


def test__qsize():
    queue = pool.Queue()
    assert queue._qsize() == 0, "size should be 0"
    queue._put("1")
    assert queue._qsize() == 1, "size should be 1"


def test__empty():
    queue = pool.Queue()
    assert queue._empty() is True, "empty should be true"
    queue._put("1")
    assert queue._empty() is False, "empty should be false"


def test__full():
    queue = pool.Queue()
    assert queue._full() is False, "full should be false"
    queue._put("1")
    assert queue._full() is False, "full should be False"


def test__put():
    queue = pool.Queue()
    queue._put("a")
    assert queue._qsize() == 1, "size should be 1 after put one item"


def test__get():
    queue = pool.Queue()
    queue._put("a")
    assert queue._get() == "a", "value should be a"


def test_qsize():
    queue = pool.Queue()
    assert queue.qsize() == 0, "size should be 0"


# @pytest.mark.skip(reason="skip now")
def test_empty():
    queue = pool.Queue()
    assert queue.empty() is True, "empty should be true"


# @pytest.mark.skip(reason="skip now")
def test_full():
    queue = pool.Queue()
    assert queue.full() is False, "full should be false"


# @pytest.mark.skip(reason="skip now")
def test_put():
    queue = pool.Queue()
    queue.put("a")
    assert queue.qsize() == 1, "size should be 1 after put one item"


# @pytest.mark.skip(reason="skip now")
def test_get():
    queue = pool.Queue()
    queue.put("a")
    assert queue.get() == "a", "value should be a"


def test_putnowait():
    queue = pool.Queue()
    queue.put_nowait("a")
    assert queue.get() == "a", "value should be a"


def test_getnowait():
    queue = pool.Queue()
    queue.put_nowait("a")
    assert queue.get_nowait() == "a", "value should be a"


def test_put_timeout():
    queue = pool.Queue()
    queue.put("a", timeout=2)
    assert queue.get() == "a", "value should be a"


def test_get_timeout():
    queue = pool.Queue()
    queue.put("a", timeout=2)
    assert queue.get(timeout=2) == "a", "value should be a"


import pytest
import pool


def test__qsize():
    queue = pool.Queue()
    assert queue._qsize() == 0, "size should be 0"


def test__empty():
    queue = pool.Queue()
    assert queue._empty() is True, "empty should be true"


def test__full():
    queue = pool.Queue()
    assert queue._full() is False, "full should be false"


def test__put():
    queue = pool.Queue()
    queue._put("a")
    assert queue._qsize() == 1, "size should be 1 after put one item"


def test__get():
    queue = pool.Queue()
    queue._put("a")
    assert queue._get() == "a", "value should be a"

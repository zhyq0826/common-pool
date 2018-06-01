from collections import deque
import threading
import time


class Empty(Exception):
    "Exception raised by Queue.get(block=0)/get_nowait()."

    pass


class Full(Exception):
    "Exception raised by Queue.put(block=0)/put_nowait()."

    pass


class Queue(object):

    def __init__(self, maxsize=0):
        """Initialize a queue object with a given maximum size.
        If `maxsize` is <= 0, the queue size is infinite.
        """
        # mutex must be held whenever the queue is mutating.  All methods
        # that acquire mutex must release it before returning.  mutex
        # is shared between the two conditions, so acquiring and
        # releasing the conditions also acquires and releases mutex.
        self._init(maxsize)
        self.mutex = threading.RLock()
        # Notify not_empty whenever an item is added to the queue; a
        # thread waiting to get is notified then.
        self.not_empty_c = threading.Condition(self.mutex)
        # Notify not_full whenever an item is removed from the queue;
        # a thread waiting to put is notified then.
        self.not_full_c = threading.Condition(self.mutex)

    def qsize(self):
        """Return the approximate size of the queue (not reliable!)."""
        self.mutex.acquire()
        n = self._qsize()
        self.mutex.release()
        return n

    def empty(self):
        """Return True if the queue is empty, False otherwise (not
        reliable!)."""

        self.mutex.acquire()
        n = self._empty()
        self.mutex.release()
        return n

    def full(self):
        """Return True if the queue is full, False otherwise (not
        reliable!)."""

        self.mutex.acquire()
        n = self._full()
        self.mutex.release()
        return n

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional args `block` is True and `timeout` is None (the
        default), block if necessary until a free slot is
        available. If `timeout` is a positive number, it blocks at
        most `timeout` seconds and raises the ``Full`` exception if no
        free slot was available within that time.  Otherwise (`block`
        is false), put an item on the queue if a free slot is
        immediately available, else raise the ``Full`` exception
        (`timeout` is ignored in that case).
        """
        self.not_full_c.acquire()
        try:
            if not block:
                if self._full():
                    raise Full()
            elif timeout is None:
                while self._full():
                    # wait for remove action to notify
                    self.not_full_c.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = time.time() + timeout
                while self._full():
                    remaining = time.time() - endtime
                    if remaining <= 0:
                        raise Full()
                    self.not_full_c.wait(remaining)
            self._put(item)
            # not empty condition notify to other thread to get
            # By default,
            # wake up one thread waiting on this condition, if any
            self.not_empty_c.notify()
        finally:
            self.not_full_c.release()

    def put_nowait(self, item):
        """Put an item into the queue without blocking.

        Only enqueue the item if a free slot is immediately available.
        Otherwise raise the ``Full`` exception.
        """
        return self.put(item, False)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args `block` is True and `timeout` is None (the
        default), block if necessary until an item is available. If
        `timeout` is a positive number, it blocks at most `timeout`
        seconds and raises the ``Empty`` exception if no item was
        available within that time.  Otherwise (`block` is false),
        return an item if one is immediately available, else raise the
        ``Empty`` exception (`timeout` is ignored in that case).
        """
        self.not_empty_c.acquire()
        try:
            if not block:
                if self._empty():
                    raise Empty()
            elif timeout is None:
                while self._empty():
                    self.not_empty_c.wait()
            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = time.time() - timeout
                while self._empty():
                    remaining = time.time() - endtime
                    if remaining <= 0:
                        raise Empty()
                    self.not_empty_c.wait(remaining)
            item = self._get()
            self.not_full_c.notify()
            return item
        finally:
            self.not_empty_c.release()

    def get_nowait(self):
        """Remove and return an item from the queue without blocking.

        Only get an item if one is immediately available. Otherwise
        raise the ``Empty`` exception.
        """

        return self.get(False)

    # Initialize the queue representation
    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = deque()

    def _qsize(self):
        return len(self.queue)

    # Check whether the queue is empty
    def _empty(self):
        return not self.queue

    # Check whether the queue is full
    def _full(self):
        return self.maxsize > 0 and len(self.queue) == self.maxsize

    # Put a new item in the queue
    def _put(self, item):
        self.queue.append(item)

    # Get an item from the queue
    def _get(self):
        return self.queue.popleft()


class Pool(object):


    def __init__(self, creator, pool_size=5, timeout=30, max_overflow=10):
        """
        :args creator caller class for connection
        :args timeout for pool get connection timeout
        :args max_overflow max allowd overflow
        """
        self.creator = creator
        self._pool = Queue()
        self._timeout = timeout
        # if pool size overflow
        self._overflow = 0 - pool_size
        self._max_overflow = max_overflow
        self._overflow_lock = threading.Lock()

    def connect(self):
        """get a connection from pool
        """
        return _ConnectionProxy().factory(self)

    def _get_conn(self):
        """internal get connection
        """
        user_overflow = self._max_overflow > -1
        try:
            wait = user_overflow and self._overflow > self._max_overflow
            # no block get
            return self._pool.get(wait, self._timeout)
        except Empty:
            pass

        if user_overflow and self._overflow >= self._max_overflow:
            if not wait:
                return self._get_conn()
            else:
                raise Exception("overflow")

        if self._inc_overflow():
            try:
                return _ConnectionProxy(self)
            except Exception, e:
                self._dec_overflow()
        else:
            # greater than max overflow
            return self._get_conn()

    def _return_conn(self, proxy):
        """return connection to pool
        """
        try:
            self._pool.put(proxy, False)
        except sqla_queue.Full:
            try:
                # free connection source
                proxy.close_connection()
            finally:
                pass

    def _inc_overflow(self):
        if self._max_overflow == -1:
            self._overflow += 1
            return True
        with self._overflow_lock:
            if self._overflow < self._max_overflow:
                self._overflow += 1
                return True
            else:
                return False

    def _dec_overflow(self):
        if self._max_overflow == -1:
            self._overflow -= 1
            return True
        with self._overflow_lock:
            self._overflow -= 1
            return True


class _ConnectionProxy(object):

    def __init__(self, pool):
        self._pool = pool
        self.connection = None
    
    @classmethod
    def factory(cls, pool):
        proxy = pool._get_conn()
        try:
            connection = proxy.get_connection()
        except Exception as err:
            raise Exception("get connection failed")

        return proxy

    def get_connection(self):
        if self.connection is None:
            self.__connect()

    def __connect(self):
        try:
            self.connection = self._pool.creator()
        except Exception, e:
            raise Exception("create connection failed")

    def close(self):
        """proxy close connection then return connecton to pool"""
        self._pool._return_conn(self)

    def close_connection():
        """thre real connection to close"""
        self.collection.close()
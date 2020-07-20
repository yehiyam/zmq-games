#
##  Paranoid Pirate queue
#
#   Author: Daniel Lundin <dln(at)eintr(dot)org>
#

from collections import OrderedDict
import time

import zmq

HEARTBEAT_LIVENESS = 3     # 3..5 is reasonable
HEARTBEAT_INTERVAL = 1.0   # Seconds

#  Paranoid Pirate Protocol constants
PPP_READY = b"\x01"      # Signals worker is ready
PPP_HEARTBEAT = b"\x02"  # Signals worker heartbeat

class Worker(object):
    def __init__(self, address):
        self.address = address
        self.expiry = time.time() + HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS

class WorkerQueue(object):
    def __init__(self):
        self.queue = OrderedDict()

    def ready(self, worker):
        self.queue.pop(worker.address, None)
        self.queue[worker.address] = worker

    def purge(self):
        """Look for & kill expired workers."""
        t = time.time()
        expired = []
        for address, worker in self.queue.items():
            if t > worker.expiry:  # Worker expired
                expired.append(address)
        for address in expired:
            print("W: Idle worker expired: %s" % address)
            self.queue.pop(address, None)

    def next(self):
        address, worker = self.queue.popitem(False)
        return address

class ClientQueue(object):
    def __init__(self):
        super().__init__()
        context = zmq.Context(1)
        self._frontend = context.socket(zmq.ROUTER) # ROUTER
        self._backend = context.socket(zmq.ROUTER)  # ROUTER
        # self._frontend.bind("inproc://proxy") # For clients
        self.port = self._frontend.bind_to_random_port("tcp://*") # For clients

        self._backend.bind("tcp://*:5556")  # For workers

    def start(self):
        

        poll_workers = zmq.Poller()
        poll_workers.register(self._backend, zmq.POLLIN)

        poll_both = zmq.Poller()
        poll_both.register(self._frontend, zmq.POLLIN)
        poll_both.register(self._backend, zmq.POLLIN)

        workers = WorkerQueue()

        heartbeat_at = time.time() + HEARTBEAT_INTERVAL

        while True:
            if len(workers.queue) > 0:
                poller = poll_both
            else:
                poller = poll_workers
            socks = dict(poller.poll(HEARTBEAT_INTERVAL * 1000))

            # Handle worker activity on self._backend
            if socks.get(self._backend) == zmq.POLLIN:
                # Use worker address for LRU routing
                frames = self._backend.recv_multipart()
                if not frames:
                    break

                address = frames[0]
                workers.ready(Worker(address))

                # Validate control message, or return reply to client
                msg = frames[1:]
                if len(msg) == 1:
                    if msg[0] not in (PPP_READY, PPP_HEARTBEAT):
                        print("E: Invalid message from worker: %s" % msg)
                else:
                    self._frontend.send_multipart(msg)

                # Send heartbeats to idle workers if it's time
                if time.time() >= heartbeat_at:
                    for worker in workers.queue:
                        msg = [worker, PPP_HEARTBEAT]
                        self._backend.send_multipart(msg)
                    heartbeat_at = time.time() + HEARTBEAT_INTERVAL
            if socks.get(self._frontend) == zmq.POLLIN:
                frames = self._frontend.recv_multipart()
                if not frames:
                    break

                frames.insert(0, workers.next())
                self._backend.send_multipart(frames)

            workers.purge()

if __name__ == "__main__":
    queue=ClientQueue()
    queue.start()
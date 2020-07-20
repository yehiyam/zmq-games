#
#  Lazy Pirate client
#  Use zmq_poll to do a safe request-reply
#  To run, start lpserver and then randomly kill/restart it
#
#   Author: Daniel Lundin <dln(at)eintr(dot)org>
#
import logging
import sys
import zmq
import os
import time
from threading import Thread
import msgpack

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

REQUEST_TIMEOUT = 2500
REQUEST_RETRIES = 3
CLIENT_ID=os.environ.get('CLIENT_ID')
DATA_SIZE=int(os.environ.get('DATA_SIZE','1000'))
print('DATA_SIZE=',DATA_SIZE)
# SERVER_ENDPOINT = "inproc://proxy"
SERVER_ENDPOINT = "tcp://localhost:"


class Client(object):
    def __init__(self,port):
        super().__init__()
        self.port=port
        logging.info("Connecting to server…")
        self.context = zmq.Context()
        self.client = self.context.socket(zmq.REQ)
        self.client.connect(SERVER_ENDPOINT+str(self.port))

    def send(self, item):
                

        

        # times = []
        # startTime = time.time()
        # startCount=0
        # curTime=time.time()
        # diff=curTime-startTime
        # if (diff>5):
        #     startTime=curTime
        #     sequenceDiff=sequence-startCount
        #     startCount=sequence
        #     print("got {count} messages in {diff} seconds".format(count=sequenceDiff, diff=diff))
        #     print("thats {mps} messages per second".format(mps=sequenceDiff/diff))

        seq=item.get('seq')
        data=item.get('data')
        request = {'seq':str(seq).encode(),'data':data}
        encoded = msgpack.packb(request)
        # logging.info("Sending (%s)", request)
        self.client.send(encoded)

        retries_left = REQUEST_RETRIES
        while True:
            if (self.client.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                reply = self.client.recv()
                # print('got reply',reply)
                if int(reply) == seq:
                    # logging.info("Server replied OK (%s)", reply)
                    break
                else:
                    logging.error("Malformed reply from server: %s", reply)
                    continue

            retries_left -= 1
            logging.warning("No response from server")
            # Socket is confused. Close and remove it.
            self.client.setsockopt(zmq.LINGER, 0)
            self.client.close()
            if retries_left == 0:
                logging.error("Server seems to be offline, abandoning")
                # sys.exit()

            logging.info("Reconnecting to server…")
            # Create new connection
            self.client = self.context.socket(zmq.REQ)
            self.client.connect(SERVER_ENDPOINT+str(self.port))
            logging.info("Resending (%s)", request.get('seq'))
            self.client.send(encoded)


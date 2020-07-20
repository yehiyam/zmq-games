#
#  Lazy Pirate client
#  Use zmq_poll to do a safe request-reply
#  To run, start lpserver and then randomly kill/restart it
#
#   Author: Daniel Lundin <dln(at)eintr(dot)org>
#
import itertools
import logging
import sys
import zmq
import os
import time
from threading import Thread
import msgpack

from clientQueue import ClientQueue
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

    def start(self):
                
        context = zmq.Context()

        logging.info("Connecting to server…")
        client = context.socket(zmq.REQ)
        client.connect(SERVER_ENDPOINT+str(self.port))

        times = []
        startTime = time.time()
        startCount=0
        for sequence in itertools.count(startCount):
            curTime=time.time()
            diff=curTime-startTime
            if (diff>5):
                startTime=curTime
                sequenceDiff=sequence-startCount
                startCount=sequence
                print("got {count} messages in {diff} seconds".format(count=sequenceDiff, diff=diff))
                print("thats {mps} messages per second".format(mps=sequenceDiff/diff))
            request = {'seq':str(sequence).encode(),'data':b'\xdd'*DATA_SIZE}
            encoded = msgpack.packb(request)
            # logging.info("Sending (%s)", request)
            client.send(encoded)

            retries_left = REQUEST_RETRIES
            while True:
                if (client.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                    reply = client.recv()
                    if int(reply) == sequence:
                        # logging.info("Server replied OK (%s)", reply)
                        break
                    else:
                        logging.error("Malformed reply from server: %s", reply)
                        continue

                retries_left -= 1
                logging.warning("No response from server")
                # Socket is confused. Close and remove it.
                client.setsockopt(zmq.LINGER, 0)
                client.close()
                if retries_left == 0:
                    logging.error("Server seems to be offline, abandoning")
                    # sys.exit()

                logging.info("Reconnecting to server…")
                # Create new connection
                client = context.socket(zmq.REQ)
                client.connect(SERVER_ENDPOINT+str(self.port))
                logging.info("Resending (%s)", request.get('seq'))
                client.send(encoded)

if __name__ == "__main__":
    queue=ClientQueue()
    client=Client(port=queue.port)
    thread=Thread(target=queue.start)
    thread.start()
    client.start()
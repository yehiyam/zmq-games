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
import queue

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
        self.queue=queue.Queue()
        self.pendingQueue={}

    def start(self):
                
        context = zmq.Context()

        logging.info("Connecting to server…")
        client = context.socket(zmq.REQ)
        client.connect(SERVER_ENDPOINT+str(self.port))

        times = []
        startTime = time.time()
        count=0
        while True:
            try:
                item=self.queue.get(block=False)
            except Exception as e:
                item=None
            if (item):
                seq=str(item.get('seq')).encode()
                data=item.get('data')
                self.pendingQueue[seq]=data
                request = {'seq':seq,'data':data}
                encoded = msgpack.packb(request)
                client.send(encoded)
                count=count+1
            curTime=time.time()
            diff=curTime-startTime
            if (diff>5):
                startTime=curTime
                sequenceDiff=count
                count=0
                print("got {count} messages in {diff} seconds".format(count=sequenceDiff, diff=diff))
                print("thats {mps} messages per second".format(mps=sequenceDiff/diff))
            retries_left = REQUEST_RETRIES
            while True:
                if (client.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                    reply = client.recv()
                    retSeq=int(reply)
                    pendingItem=self.pendingQueue.get(reply)
                    if (pendingItem):
                        self.pendingQueue.pop('reply',None)
                        break
                    else:
                        logging.error("Malformed reply from server: %s", reply)
                        continue

                retries_left -= 1
                logging.warning("No response from server")
                if retries_left == 0:
                    # Socket is confused. Close and remove it.
                    client.setsockopt(zmq.LINGER, 0)
                    print('close')
                    client.close()
                    logging.error("Server seems to be offline, abandoning")
                    # sys.exit()

                    logging.info("Reconnecting to server…")
                    # Create new connection
                    client = context.socket(zmq.REQ)
                    print('connect')
                    client.connect(SERVER_ENDPOINT+str(self.port))
                    break
                # logging.info("Resending (%s)", request.get('seq'))
                # client.send(encoded)

if __name__ == "__main__":
    clientQueue=ClientQueue()
    client=Client(port=clientQueue.port)
    thread=Thread(target=clientQueue.start)
    thread.setDaemon(True)
    thread.start()
    clientThread=Thread(target=client.start)
    clientThread.setDaemon(True)
    clientThread.start()
    for sequence in itertools.count():
         client.queue.put({"seq":sequence, "data":"ddd"})
         time.sleep(0.1)
import logging
from threading import Thread
from clientQueue import ClientQueue
from client import Client
import queue
import itertools
import time

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


if __name__ == "__main__":
    queue=queue.Queue()

    clientQueue=ClientQueue()
    client=Client(port=clientQueue.port)
    queueThread=Thread(target=clientQueue.start, daemon=True).start()
    def send():
        while True:
            item=queue.get()
            client.send(item)    
            queue.task_done()
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    threads = []
    for i in range(4):
        t = Thread(target=send, daemon=True)
        t.start()
        threads.append(t)
    seq=0
    startTime = time.time()
    startCount=0
    while True:
        queueSize=queue.qsize()
        
        if (queueSize>10):
            time.sleep(0.1)
        else:
            # print('sending seq',seq)
            queue.put({'seq':seq, 'data': b'\xdd'*10})
            seq=seq+1
            time.sleep(0.005)

        curTime=time.time()
        diff=curTime-startTime
        if (diff>5):
            startTime=curTime
            sequenceDiff=seq-startCount
            startCount=seq
            print("got {count} messages in {diff} seconds".format(count=sequenceDiff, diff=diff))
            print("thats {mps} messages per second".format(mps=sequenceDiff/diff))            
            print(f'queue size: {queueSize}')

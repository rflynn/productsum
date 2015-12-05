import multiprocessing
import os
import time

man = multiprocessing.Manager()

q1 = man.Queue()
q2 = man.Queue()

print dir(q1)

def worker_main(q1, q2):
    print os.getpid(), 'working'
    while True:
        item = q1.get(True)
        q2.put((os.getpid(), 'got', item))
        time.sleep(1) # simulate a "long" operation

the_pool = multiprocessing.Pool(3, worker_main,(q1, q2,))
#                            don't forget the coma here  ^

sent = 0
recv = 0

def _get_nowait(q):
    try:
        return q.get_nowait()
    except:
        return None

for i in range(5):
    q1.put('hello')
    q1.put('world')
    sent += 2
    time.sleep(1)
    x = _get_nowait(q2)
    while x:
        print x
        recv += 1
        x = _get_nowait(q2)

while recv < sent:
    print q2.get()
    recv += 1

print 'done'

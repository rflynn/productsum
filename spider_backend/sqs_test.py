# ex: set ts=4 et:

'''
test AWS SQS read/write via boto
'''

import boto3 as boto

import boto.sqs
from boto.sqs.message import RawMessage


def conn_q():

    conn = boto.sqs.connect_to_region(
        'us-east-1',
        aws_access_key_id='AKIAIJSFBGWDARVXQBSA',
        aws_secret_access_key='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')

    q = conn.create_queue('qtest1')
    q.set_message_class(RawMessage)

    print conn.get_all_queues()

    #my_queue = conn.get_queue('qtest1')

    return conn, q


def send_msg(q, body):
    m = RawMessage()
    m.set_body(body)
    q.write(m)


def handle_msgs(q, msgs):
    print len(msgs)
    for msg in msgs:
        #print msg.message_attributes
        print msg.get_body()
        #print len(msg.message_attributes['name3']['binary_value'])
        d = q.delete_message(msg)
        if not d:
            print 'delete msg failed...'


def receive_loop(conn, q, timeout_secs=3, exit_on_timeout=False):
    while True:
        msgs = conn.receive_message(q,
                    number_messages=10,
                    wait_time_seconds=timeout_secs)
        print 'msgs:', msgs
        if not msgs:
            if exit_on_timeout:
                break
        handle_msgs(q, msgs)


if __name__ == '__main__':

    conn, q = conn_q()
    send_msg(q, b'binary works in the body\xe2\x98\xba')
    send_msg(q, b'binary works in the body\xe2\x98\xba')
    receive_loop(conn, q, timeout_secs=1, exit_on_timeout=True)


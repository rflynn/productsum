# ex: set ts=4 et:

import boto3 as boto
import hashlib
from time import sleep


def get_string_from_s3(bucket, path):
    while True:
        try:
            s3 = boto.resource('s3')
            obj = s3.Object(bucket, path)
            return obj.get()['Body']
        except Exception as e:
            print e
            sleep(3)

def do_write_string_to_s3(bucket, path, contents):
    while True:
        try:
            s3 = boto.resource('s3')
            return s3.Object(bucket, path).put(Body=contents)
        except Exception as e:
            print e
            sleep(3)


def sha256_to_filename(h):
    return '%s/%s/%s/%s' % (h[0:2], h[2:4], h[4:6], h)


def contents_to_filename(contents):
    h = hashlib.sha256(contents)
    return sha256_to_filename(h.hexdigest()), h.digest()


def write_string_to_s3(bucket, contents):
    path, h = contents_to_filename(contents)
    print 'writing to bucket %s' % path
    while True:
        try:
            s3 = boto.resource('s3')
            s3.Object(bucket, path).put(Body=contents)
            return path, h
        except Exception as e:
            print e
            sleep(3)


def get_body_by_hash(bucket, sha256):
    path = sha256_to_filename(sha256)
    while True:
        try:
            s3 = boto.resource('s3')
            obj = s3.Object(bucket, path)
            return obj.get()['Body']
        except Exception as e:
            print e
            sleep(3)


def test_get_string():
    return get_string_from_s3('www.productsum.com', 'index.html').read()


if __name__ == '__main__':
    import time
    #print test_get_string()

    bucket = 'productsum-spider'
    t = str(time.time())
    path, h = write_string_to_s3(bucket, t)
    assert get_string_from_s3(bucket, path)


'''
for bucket in boto.resource('s3').buckets.all():
    print(bucket.name)
'''

'''
with open('hello.txt') as f:
    f.write('Hello, world!')

# Upload the file to S3
s3.upload_file('hello.txt', 'MyBucket', 'hello-remote.txt')
'''

'''
# Download the file from S3
s3.download_file('MyBucket', 'hello-remote.txt', 'hello2.txt')
print(open('hello2.txt').read())
'''


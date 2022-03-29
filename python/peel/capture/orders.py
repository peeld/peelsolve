import json
import httplib
import base64
from peel.util import time_util


class OrderRange(object):
    def __init__(self, row):
        self.tc_in = time_util.Timecode(str(row['in']), 29.97)
        self.tc_out = time_util.Timecode(str(row['out']), 29.97)
        self.tc_start = time_util.Timecode(str(row['startTimecode']), 29.97)
        self.creator = row['creator']
        self.notes = row['notes']
        self.company = row['company']
        self.subjects = row['subjects']
        self.take = row['take']

        if self.tc_in.h is None:
            print("Could not parse in: " + str(row['in']))

    def __str__(self):
        return str(self.take)


class Orders(object):

    def __init__(self, username, password):

        auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

        payload = {}
        hdr = {"content-type": "application/json",
               "Authorization": "Basic %s" % auth}

        conn = httplib.HTTPConnection('beta.peelcapture.com')
        conn.request('POST', '/do/api/orders', json.dumps(payload), hdr)
        response = conn.getresponse()
        data = response.read()

        self.orders = json.loads(data)

    def __iter__(self):
        return self.orders.__iter__()

    def __next__(self):
        return self.orders.__next__()

    def titles(self):
        return dict([(i['id'], i['name']) for i in self.orders])

    def ranges(self, id, take=None):
        for order in self.orders:
            if order['id'] == id:
                if take is None:
                    return [OrderRange(i) for i in order['ranges']]
                else:
                    return [OrderRange(i) for i in order['ranges'] if i['take'] == take]
        return None







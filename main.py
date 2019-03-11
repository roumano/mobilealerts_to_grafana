#! /usr/bin/env python
# coding: utf-8

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
import urllib.parse
from influxdb import InfluxDBClient
from dateutil import parser

_url = 'https://measurements.mobile-alerts.eu'
_phoneId = os.environ.get('PHONE_ID')
_db_user = 'admin'
_db_passwd = 'qUV4ingbQLJx!@845CBuo'
_db_name = mobilealerts

def getSensorName(sensor):
    if 'date' in sensor.text:
        return 'Date'
    return sensor.text


def getSummarySensor(sensor):
    return {
        'name': sensor.a.text,
        'details_url': sensor.a['href'],
        'components': {getSensorName(component.h5): component.h4.text
                       for component in sensor.find_all('div', 'sensor-component')},
        'last_24h': getDetail(sensor.a['href']),
    }


def getSummary():
    r = requests.Session()
    r.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64…) Gecko/20100101 Firefox/65.0'})
    r = requests.get(
        '{}/Home/SensorsOverview?phoneid={}'.format(_url, _phoneId), )
    return [getSummarySensor(sensor)
            for sensor in BeautifulSoup(r.text, 'html.parser').find_all('div', 'sensor')]


def getDetail(url,date = None):
    if date is None:
	    date = datetime.now() - timedelta(days=1)
    fromepoch = date.replace(hour=0,minute=1,second=0,microsecond=0).timestamp()
    fromepochtest = date.replace(hour=0,minute=1,second=0,microsecond=0)
    toecpoch = date.replace(hour=23,minute=59,second=59,microsecond=999999).timestamp()
    toecpochtest = date.replace(hour=23,minute=59,second=59,microsecond=999999)
    print (fromepochtest)
    print (toecpochtest)
    fromepoch2 = urllib.parse.quote_plus(str(fromepochtest.strftime("%d/%m/%Y+%H:%M"))).replace('%2B','+')
    toecpoch2 = urllib.parse.quote_plus(str(toecpochtest.strftime("%d/%m/%Y+%H:%M"))).replace('%2B','+')
    # '09%2F03%2F2019%3A%3A00%3A00'
    sleep(1.1) # Time in seconds.
    # from=09%2F03%2F2019+00%3A01&to=09%2F03%2F2019+23%3A59
    # print (urllib.parse.quote_plus(fromdate).replace('%2B','+'))
    # 09%2F03%2F2019+00%3A00

    # http://krypted.com/utilities/html-encoding-reference/
    # %2F == /
    # %3A == ::
    # from=09/03/2019+00:01 to=09/03/2019+23::59
    # print (fromepoch.strftime("%d/%m/%y::%H:%M"))
    # 09/03/19::00:00
    r = requests.post('{}{}'.format(_url, url), data={
                      'fromepoch': fromepoch, 'toepoch': toecpoch, 'from': fromepoch2, 'to': toecpoch2, 'pagesize': 250})

    soup = BeautifulSoup(r.text, 'html.parser').find(
        'form', {'id': 'MeasurementDetails'})

    header = [getSensorName(h) for h in soup.select('table thead tr th')]

    return [{header[i]: td.text for i, td in enumerate(line.find_all('td'))}
                   for line in soup.select('table tbody tr')]

def getDBLastInfo():
    client = InfluxDBClient(host='localhost', port=8086, username=_db_user , password=_db_passwd )
    client.switch_database(_db_name)
    db = client.query('SELECT "value" FROM "temperature" ORDER by time DESC LIMIT 1')
    points = db.get_points()
    #dblastpoint=point['time']
    return parser.parse(point['time'])

if __name__ == "__main__":
	dblastpoint = getDBLastInfo()
	# get detail of days from dblastpoint + 1 to now -1d
	
    print(getSummary())

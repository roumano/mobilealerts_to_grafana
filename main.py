#! /usr/bin/env python
# coding: utf-8

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
from random import uniform
from influxdb import InfluxDBClient
from dateutil import parser

_url = 'https://measurements.mobile-alerts.eu'
_phoneId = os.environ.get('PHONE_ID')
_date = os.environ.get('DATE')
_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'}
_db_user = 'admin'
_db_passwd = 'qUV4ingbQLJx!@845CBuo'
_db_name = 'mobilealerts'

def getSensorName(sensor):
    if 'date' in sensor.text:
        return 'Date'
    return sensor.text




def getSummary(date):
    r = requests.get(
        '{}/Home/SensorsOverview?phoneid={}'.format(_url, _phoneId), headers=_headers)
    return [getDetail(sensor,date)
            for sensor in BeautifulSoup(r.text, 'html.parser').find_all('div', 'sensor')]





def getDetail(sensor, date = None):
    sleep (uniform(1, 3))
    post_data = {
        'fromepoch': int(date.replace(hour=0,minute=1,second=0,microsecond=0).timestamp()),
        'toepoch': int(date.replace(hour=23,minute=59,second=59,microsecond=999999).timestamp()),
        'pagesize': 250
    }
    r = requests.post('{}{}'.format(_url, sensor.a['href']), data=post_data, headers=_headers)

    soup = BeautifulSoup(r.text, 'html.parser').find(
        'form', {'id': 'MeasurementDetails'})

    header = [getSensorName(h) for h in soup.select(
        'table thead tr th:nth-child(1n+2)')]

    data = []
    for line in soup.select('table tbody tr'):
        _date2 = datetime.strptime(line.select('td')[0].text, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%SZ')
        data.append( {
            "measurement": "mobilealerts",
            "fields": {header[i]: td.text.strip('%C ') for i, td in enumerate(line.select('td:nth-child(1n+2)'))},
            "tags": {
                "location": sensor.a.text,
            },
            "time": _date2,
        } )
    publishIntoDb(data)


def publishIntoDb(data):
    print(data)
    # TODO: write here code to publish into influxDb
    client = InfluxDBClient(host='localhost', port=8086, username=_db_user , password=_db_passwd )
    client.switch_database(_db_name)
    client.write_points(data, database=_db_name, time_precision='s')



if __name__ == "__main__":
    if _date is None:
        date = datetime.now() - timedelta(days=1)
    else:
        date = parser.parse(_date)
    getSummary(date)

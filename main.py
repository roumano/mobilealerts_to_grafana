#! /usr/bin/env python
# coding: utf-8

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
from random import uniform

_url = 'https://measurements.mobile-alerts.eu'
_phoneId = os.environ.get('PHONE_ID')
_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'}

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
    r = requests.get(
        '{}/Home/SensorsOverview?phoneid={}'.format(_url, _phoneId), headers=_headers)
    return [getSummarySensor(sensor)
            for sensor in BeautifulSoup(r.text, 'html.parser').find_all('div', 'sensor')]


def getDetail(url,date = None):
    if date is None:
        date = datetime.now() - timedelta(days=1)
    now = datetime.now()
    fromepoch = int(date.replace(hour=0,minute=1,second=0,microsecond=0).timestamp())
    toecpoch = int(date.replace(hour=23,minute=59,second=59,microsecond=999999).timestamp())
    sleep (uniform(1, 3)) # Time in seconds. random between 1 & 3
    r = requests.post('{}{}'.format(_url, url), data={
                      'fromepoch': fromepoch, 'toepoch': toecpoch, 'pagesize': 250}, headers=_headers)

    soup = BeautifulSoup(r.text, 'html.parser').find(
        'form', {'id': 'MeasurementDetails'})

    header = [getSensorName(h) for h in soup.select('table thead tr th')]

    return [{header[i]: td.text for i, td in enumerate(line.find_all('td'))}
                   for line in soup.select('table tbody tr')]


if __name__ == "__main__":
    print(getSummary())

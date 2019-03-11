#! /usr/bin/env python
# coding: utf-8

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

_url = 'https://measurements.mobile-alerts.eu'
_phoneId = os.environ.get('PHONE_ID')


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
        '{}/Home/SensorsOverview?phoneid={}'.format(_url, _phoneId))
    return [getSummarySensor(sensor)
            for sensor in BeautifulSoup(r.text, 'html.parser').find_all('div', 'sensor')]


def getDetail(url):
    now = datetime.now()
    fromepoch = (now - timedelta(days=1)).timestamp()
    toecpoch = now.timestamp()
    r = requests.post('{}{}'.format(_url, url), data={
                      'fromepoch': fromepoch, 'toepoch': toecpoch, 'pagesize': 200})

    soup = BeautifulSoup(r.text, 'html.parser').find(
        'form', {'id': 'MeasurementDetails'})

    header = [getSensorName(h) for h in soup.select('table thead tr th')]

    return [{header[i]: td.text for i, td in enumerate(line.find_all('td'))}
                   for line in soup.select('table tbody tr')]


if __name__ == "__main__":
    print(getSummary())

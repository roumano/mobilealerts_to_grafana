#! /usr/bin/env python
# coding: utf-8

import os
import sys
import requests
import argparse
import json
import pytz
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date, timezone
from time import sleep
from random import uniform
from influxdb import InfluxDBClient
from dateutil import parser
from pathlib import Path

_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'}

PFILE = "/.params"

# Sub to return format wanted by linky.py
def _dayToStr(date):
    return date.strftime("%d/%m/%Y")

# Open file with params for influxdb, enedis API and HC/HP time window
def _openParams(pfile):
    # Try to load .params then programs_dir/.params
    if os.path.isfile(os.getcwd() + pfile):
        p = os.getcwd() + pfile
    elif os.path.isfile(os.path.dirname(os.path.realpath(__file__)) + pfile):
        p = os.path.dirname(os.path.realpath(__file__)) + pfile
    else:
        if (os.getcwd() + pfile != os.path.dirname(os.path.realpath(__file__)) + pfile):
            logging.error('file %s or %s not exist', os.path.realpath(os.getcwd() + pfile) , os.path.dirname(os.path.realpath(__file__)) + pfile)
        else:
            logging.error('file %s not exist', os.getcwd() + pfile )
        sys.exit(1)
    try:
        f = open(p, 'r')
        try:
            array = json.load(f)
        except ValueError as e:
            logging.error('decoding JSON has failed', e)
            sys.exit(1)
    except IOError:
        logging.error('cannot open %s', p)
        sys.exit(1)
    else:
        f.close()
        return array

def getSensorName(sensor):
    if 'date' in sensor.text:
        return 'Date'
    return sensor.text


def getSummary(date):
    r = requests.get(
        '{}/Home/SensorsOverview?phoneid={}'.format(params['mobile-alerts']['url'], params['mobile-alerts']['phoneId']), headers=_headers)
    data = []
    for sensor in BeautifulSoup(r.text, 'html.parser').find_all('div', 'sensor'):
        getDetail(sensor,date,data)

    publishIntoDb(data)
    WriteToFile(date,data)

def getDetail(sensor, date, data):
    local = pytz.timezone ("Europe/Paris")
    default = 0.0

    sleep (uniform(5, 9))
        #'toepoch': int(date.replace(hour=23,minute=59,second=59,microsecond=999999).timestamp()),
    post_data = {
        'fromepoch': int(datetime.combine(date, datetime.min.time()).timestamp()),
        'toepoch': int(datetime.combine(date, datetime.max.time()).timestamp()),
        'pagesize': 250
    }
    r = requests.post('{}{}'.format(params['mobile-alerts']['url'], sensor.a['href']), data=post_data, headers=_headers)

    soup = BeautifulSoup(r.text, 'html.parser').find(
        'form', {'id': 'MeasurementDetails'})

    header = [getSensorName(h) for h in soup.select(
        'table thead tr th:nth-of-type(1n+2)')]

    #print(header)
    # ['Température', 'Hygrométrie']
    for i, type in enumerate(header):
        #print(type)
        if type == 'Capteur de température':
            fields = 'Température'
            location = 'piscine'
        else:
            location = sensor.a.text
            fields = type

        for line in soup.select('table tbody tr'):
            value = line.select('td')[i+1].text.strip('% C')
            if value == '---':
                continue
            else:
                _date2 = datetime.strptime(line.select('td')[0].text, '%d/%m/%Y %H:%M:%S')
                # is_dst=None is not working anymore, use True or False instead ? 
                # http://pytz.sourceforge.net/
                #_date3 = local.localize(_date2, is_dst=None).astimezone(pytz.utc).strftime ('%Y-%m-%dT%H:%M:%SZ')
                _date3 = local.localize(_date2, is_dst=False).astimezone(pytz.utc).strftime ('%Y-%m-%dT%H:%M:%SZ')
                # Bad data ? :
                try:
                    value = float(value.replace(',','.'))
                except ValueError:
                    print ('Error with', line , ',unable to convert' , value , 'as float for the type:', type)
                    continue

                if 'resille' in params and location == 'dehors' and fields == 'Température':
                    # Add into DB : ecart & consigne from .params

                    data.append( {
                        "measurement": "mobilealerts",
                        "fields": {
                          fields: float(value),
                          "consigne": int(params['resille']['consigne']),
                          "ecart": int(params['resille']['ecart']),
                        },
                        "tags": { "location": location, },
                        "time": _date3,
                        } )
                else:
                    data.append( {
                        "measurement": "mobilealerts",
                        "fields": {fields: float(value)},
                        "tags": { "location": location, },
                        "time": _date3,
                        } )

def publishIntoDb(data):
    client = InfluxDBClient(host=params['influx']['host'], port=params['influx']['port'], username=params['influx']['username'] , password=params['influx']['password'] )
    client.switch_database(params['influx']['db'])
    client.write_points(data, database=params['influx']['db'], time_precision='s')

def getDBLastInfo():
    dateinfluxdb = None
    client = InfluxDBClient(host=params['influx']['host'], port=params['influx']['port'], username=params['influx']['username'] , password=params['influx']['password'] )
    client.switch_database(params['influx']['db'])
    db = client.query('SELECT "Température" FROM "mobilealerts" ORDER by time DESC LIMIT 1')
    for item in db.get_points():
        dateinfluxdb = item['time']
    if dateinfluxdb is None:
        print('Unable to get data in influxdb, the database is empty?')
        print('use the --date argument ')
        sys.exit(1)
    return dateinfluxdb

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def PushHeureCreuse(date):
    # For each temperature where location = dehors add a field heureCreuse (0 or 1 )
    data = []
    begin = datetime.combine(date, datetime.min.time())
    end = datetime.combine(date, datetime.max.time())
    # UTC time so - 2 hours ...
    #heureCreuseDebut = begin.replace(hour=1,minute=40)
    heureCreuseDebut = begin.replace(hour=23,minute=40) - timedelta(days=1)
    heureCreuseFin = begin.replace(hour=6,minute=10)
    heureCreuse2Debut = begin.replace(hour=10,minute=10)
    heureCreuse2Fin = begin.replace(hour=11,minute=40)
    #print("heureCreuseDebut " , heureCreuseDebut)
    #print("heureCreuseFin " , heureCreuseFin)
    client = InfluxDBClient(host=params['influx']['host'], port=params['influx']['port'], username=params['influx']['username'] , password=params['influx']['password'] )
    client.switch_database(params['influx']['db'])
    query = "SELECT \"Température\" FROM \"mobilealerts\" WHERE location ='dehors' AND time > '" + begin.strftime("%Y-%m-%d %H:%M:%S") + "' AND time < '" + end.strftime("%Y-%m-%d %H:%M:%S") + "' ORDER by time"
    #db = client.query('SELECT "Température" FROM "mobilealerts" WHERE location =\'dehors\' AND time > \'2019-04-02 00:00:00.000\' AND time < \'2019-04-02 23:59:59.999\' ORDER by time')
    db = client.query(query)

    for item in db.get_points():
        db_date = datetime.strptime(item['time'],'%Y-%m-%dT%H:%M:%SZ')
        #print("db_date " , db_date)
        if ( db_date > heureCreuseDebut and db_date < heureCreuseFin) or ( db_date > heureCreuse2Debut and db_date < heureCreuse2Fin ):
            heureCreuse = 1
        else:
            heureCreuse = 0
        data.append( {
            "measurement": "mobilealerts",
            "fields": {"heureCreuse": heureCreuse},
            "tags": {
                "location": "dehors",
            },
            "time": item['time'],
        } )
    publishIntoDb(data)


def WriteToFile(date, data):
    # Only if date is not today (today the file will not be complete ...)
    if (date < datetime.now().date()):
        with open(str(os.getcwd()) + "/data/" + date.strftime("%Y-%m-%d") + ".txt", mode='w') as f:
            #json.dump(data,f)
            # Better output
            f.write(json.dumps(data, indent=1))
        f.close()

if __name__ == "__main__":
    # Date will be a class datetime.date
    # To convert into datetime : datetime.combine(date, datetime.min.time())
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='date in format YYYY-MM-DD')
    args = parser.parse_args()
    params = _openParams(PFILE)
    # params['influx']['username']
    # logging.info("logged in InfluxDB Server Host %s succesfully", params['influx']['host'])
    #

    if args.date is None:
        # Connect to influxdb, get the lastest entry & add 1 days
        start_date = datetime.strptime(getDBLastInfo(), '%Y-%m-%dT%H:%M:%SZ').date() + timedelta(days=1)
        end_date = datetime.now().date()
        #end_date = datetime.now().date() - timedelta(days=1)
        for single_date in daterange(start_date, end_date):
            try:
                with open(str(os.getcwd()) + "/data/" + single_date.strftime("%Y-%m-%d") + ".txt") as f:
                    data = json.load(f)
                    f.close()
                    print ("Reading data from Mobile-alerts/data/" + single_date.strftime("%Y-%m-%d") + ".txt")
                    publishIntoDb(data)
                    PushHeureCreuse(single_date)

            # Otherwise get data from internet
            except FileNotFoundError:
                print("Fetch Data for date ", single_date.strftime("%Y-%m-%d"))
                # print("date est au format ", type(single_date.strftime("%Y-%m-%d")))
                getSummary(single_date)
                PushHeureCreuse(single_date)
    else:
        date = datetime.strptime(args.date, '%Y-%m-%d').date()
        print("Fetch Data for date ", date.strftime("%Y-%m-%d"))
        # Read the file as source
        try:
            with open(str(os.getcwd()) + "/data/" + date.strftime("%Y-%m-%d") + ".txt") as f:
                data = json.load(f)
            f.close()
            print ("Reading data from Mobile-alerts/data/" + date.strftime("%Y-%m-%d") + ".txt")
            publishIntoDb(data)
            PushHeureCreuse(date)


        # Otherwise get data from internet
        except FileNotFoundError:
            getSummary(date)
            PushHeureCreuse(date)

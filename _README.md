# Command line
* From last date in influxdb to yesterday :
`PHONE_ID=... python main.py`
* a specific day
`PHONE_ID=... python main.py --date 2019-03-17 `
* today :
PHONE_ID=335626731851 python3 ~/Dropbox/Mobile-alerts/main.py --date $(date "+%Y-%m-%d" --date today)


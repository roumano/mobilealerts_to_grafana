# Why
Lacross Technology deliver very good quality of temperature sensor.
But GUI are not very good and can't see graphs or trends and datadata are removed after a certain period

This small python programs parse your data in order to put them into a influxdb server.
It's also save the data into a json file per day

# Configuration
you have to set few parametres into a `.params` file, like on this exemple:
```
{
    "mobile-alerts":
    {
        "url":     "https://measurements.mobile-alerts.eu",
        "phoneId": "1234567890"
    },
    "influx":
    {
        "host":			"localhost",
        "port":			8086,
        "db":			"mobilealerts",
        "username":		"admin",
        "password":		"XXXX",
        "ssl":			false,
        "verify_ssl":	false
    },
    "hc":
    [{
        "start":   { "h": 1, "m": 40 },
        "end":     { "h": 8, "m": 10 }
     },{
        "start":   { "h": 12, "m": 10 },
        "end":     { "h": 13, "m": 40 }
    }],
    "resille":
    {
      "consigne": "10",
      "ecart": "14"
    }
}
```

* The **resille* part is only need if you have a **Delta 55** or **Delta 50** to heat your house and want to simulte the power utilization.
* The **hc** part is only need if you have a **Heure Creuse/Heure Pleine** power supply and a **Delta

# Command line
* From last date in influxdb to yesterday :
`python3 main.py`
* For a specific day
it's mandatory to use the programs like this the first run !
`python3 main.py --date 2019-03-17 `

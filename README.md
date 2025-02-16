# write_rna_metrics_2_db
Writing RNA metrics to postgresql
Write another micro service that uses SQLalchemy with postgresql; this micro service when fired with a call /data/pullperformancemetrics will do the following:
- will check the table performance_metrics_index for the latest index and will increase a counter by one; if index > 10000 then it will restart from 1 overwriting the contents of it: the index no and the current time YYYYMMDDHHMM;
- it will pull the JSON with performancemetrics from RNA 

```json
{
  "result": {
    "devices": [
      {
        "id": "5",
        "name": "DC1A-SFO-C8300::Marketing-Demo",
        "objects": [
          {
            "id": "xyz",
            "name": "DC1A-xyz::GigabitEthernet0/0/0.12-xyz01::xGigabitEthernet0/0/7.xyzq",
            "pluginId": "17",
            "indicators": [
              {
                "id": "xyz3",
                "name": "latency",
                "lastSeen": "1739134944000",
                "value": 187,
                "unit": "ms"
              },
              {
                "id": "xyz6",
                "name": "jitter",
                "lastSeen": "1739134944000",
                "value": 0,
                "unit": "ms"
              },
              {
                "id": "xyz59",
                "name": "loss_percentage",
                "lastSeen": "1739134944000",
                "value": 0,
                "unit": "%"
              }
            ]
          }
        ]
      }
    ]
  }
}
```
to insert data in the table performance_metrics_data deleting before inserting rows for the given foreign_key - index from performance_metrics_index table, and adding a row with the following information: index, device_id, device_name, object_id, object_name, loss_percentage, jitter, latency, current time YYYYMMDDHHMM



## build it

* If you have a mac, then run commands :

```sh
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

for win OS in powershell run
```sh
.\.venv\bin\activate
```

### run it

  * in the terminal write `flask --app app run`
  * In a browser, load the url: http://127.0.0.1:5000/

### deploy it in a cloud as a microservice using RHOS

You need to setup the env variable in RHOS for the access to the postgresql:
```
URL=postgresql://ibm_cloud_ user:pass@the.address.databases.appdomain.cloud:port/ibmclouddb
RNA=url
```


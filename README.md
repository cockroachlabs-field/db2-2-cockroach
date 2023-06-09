# DB2 to CockroachDB

### Setup 
* Setup and activate your local Python 3.x environment `venv`

```commandline
$ python -m venv venv
$ source venv/bin/activate
```

* Install dependencies

```commandline
$ pip install -r requirements.txt
```

* Optionally, install dependencies individually

```commandline
$ pip install streamlit urllib3==1.24.3
```

### Deploy

* Deploy the Streamlit service locally with 

```commandline
$ streamlit run Home.py
```

### UI

* Upload your DDL schema
* From the dropdown, multi-select, choose the type of statements to convert
* Click download button to get your new sql DDL

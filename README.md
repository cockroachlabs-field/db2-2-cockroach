# DB2 to CockroachDB

Schema conversion from DB2 to CockroachDB covers:

* schema, database
* create table
* create unique index
* create indexes

Require transformations or redesign in the business logic:

* alter table (might require redesign when working with PRIMARY/FOREIGN KEY references)
* changefeeds (example command for each table)

Not migrated:

* create sequence
* alter sequence
* create trigger
* create procedure 

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

import re
import streamlit as st
from io import BytesIO

##############################################################################
# DB2-CRDB Schema Conversion
# Provide a dynamic option to separately export statements for CockroachDB.
##############################################################################

st.title("DB2 schema conversion to CockroachDB")

# Create a list of options for the dropdown
options = ["CREATE SCHEMA", "CREATE TABLE", "ALTER TABLE", "CREATE UNIQUE INDEX", "CREATE INDEX", "DATA CAPTURE"]

kafkafmt = """INTO 'kafka://{host}:{port}'
  WITH updated, resolved;
"""

kafkaavrofmt = """INTO 'kafka://{host}:{port}'
  WITH format = avro, confluent_schema_registry = {schema_registry_address};
"""

s3fmt = """INTO 's3://{bucket_name}/{path}?AWS_ACCESS_KEY_ID={key_id}&AWS_SECRET_ACCESS_KEY={secret_access_key}&S3_STORAGE_CLASS=INTELLIGENT_TIERING' 
  WITH resolved;
"""

gsfmt = """INTO 'gs://{bucket_name}/{path}?AUTH=specified&CREDENTIALS={encoded_key}'
  WITH resolved
"""

azurefmt = """INTO 'kafka://{host}:{port}'
  WITH updated, resolved;
"""

pubsubfmt = """INTO 'gcpubsub://{project_name}?region={region}&TOPIC_NAME={topic_name}&AUTH=specified&CREDENTIALS={base64_encoded_key}'
  WITH resolved;
"""
webhookfmt = """INTO 'webhook-https://{url_webhook_endpoint}?INSECURE_TLS_SKIP_VERIFY=true'
  WITH updated;
"""

httpfmt = """INTO 'http://localhost:8080/{path}';
  WITH updated;
"""

localfmt = """INTO 'nodelocal://{directory}'
  WITH resolved;
"""

cdcsinks = {
    "Kafka": kafkafmt,
    "Kafka+AVRO": kafkaavrofmt,
    "S3": s3fmt,
    "GS": gsfmt,
    "Azure": azurefmt,
    "PubSub": pubsubfmt,
    "Webhook": webhookfmt,
    "HTTP": httpfmt,
    "Local": localfmt
}

cdcusr = {"user": "user"}

st.sidebar.subheader("Config")
# Create an upload field
uploaded_file = st.sidebar.file_uploader("1) Upload a .db2, .sql or, .ddl file:", type=['sql', 'ddl', 'db2'])

# Check if a file was uploaded
if uploaded_file:
    # Create a BytesIO object to read the file in memory
    byte_contents = BytesIO(uploaded_file.read())
    file_contents = byte_contents.read()
    text = file_contents.decode("UTF-8")



cdcselect = st.sidebar.selectbox(
    "Set a CDC Sink, sets examples on how to setup Streaming from the CockorachDB Cluster:", cdcsinks)
cdcoptions = st.sidebar.text_area("**(Optional)** Configure the CDC Sink :", value=cdcsinks[cdcselect])
cdcuser = st.sidebar.text_input("**(Optional)** CDC User:", value=cdcusr["user"])
# Create a multiselect dropdown
dropdown = st.multiselect("Select DDL statement, for CDC you must choose the `ALTER TABLE` and `DATA CAPTURE`: ",
                          options)

st.success("[CDC Sink configuration reference](https://www.cockroachlabs.com/docs/stable/create-changefeed.html)")
def detect_keywords(string):
    keywords = re.findall(r'\b[a-zA-Z0-9_\(]+\b', string)
    return keywords


# Print the selected options
if dropdown:
    ine = "IF NOT EXIST"
    tofile = "--- DB2 to CockroachDB Schema Migration \n"
    reg = "|".join(dropdown)
    regex = r'(?s)(' + reg + ').+?;'
    matches = re.finditer(regex, text, re.MULTILINE | re.DOTALL)
    print(text)
    for matchNum, match in enumerate(matches, start=1):

        for groupNum in range(0, len(match.groups())):

            if 'CREATE SCHEMA' in match.group():
                new_string = "-- CREATE DATABASE, USER, SCHEMA \n"
                regx = re.compile(r'CREATE SCHEMA (.+) AUTHORIZATION (.+);')
                matx = regx.match(match.group())
                schema_name = matx.group(1).replace('"', '').strip()
                dbuser = matx.group(2).replace('"', '').strip()
                new_string += f"CREATE DATABASE {ine} {schema_name};\n"
                new_string += f"USE {schema_name};\n"
                new_string += f"CREATE USER  {dbuser};\n"
                new_string += 'CREATE SCHEMA IF NOT EXISTS AUTHORIZATION {};\n\n'.format(schema_name,
                                                                              dbuser)
                tofile += new_string

            if 'CREATE TABLE' in match.group():
                for s in match.group().splitlines():
                    if 'CREATE TABLE' in s:
                        # st.write(s)
                        # Detect if statement contains schema definitions and tables
                        keywords = detect_keywords(s)
                        lenkeys = len(keywords)
                        if lenkeys == 3:
                            new_table = f"{keywords[0]} {keywords[1]} {ine} {keywords[2]} (\n"
                            tbl_name = keywords[2]
                            tofile += f"\n\n-- CREATE TABLE {ine} {keywords[2]} ---\n "
                        elif lenkeys == 4:
                            new_table = f"{keywords[0]} {keywords[1]} {ine} {keywords[2]}.{keywords[3]} (\n"
                            tbl_name = keywords[3]
                            print(tbl_name)
                            tofile += f"\n\n-- CREATE TABLE {ine} {keywords[2]}.{tbl_name} ---\n "
                        else:
                            print("not a valid table")

                    else:
                        if 'IN ' in s:
                            s = ""
                        if 'DATA CAPTURE CHANGES' in s:
                            s = ""
                        if "UNICODE" in s:
                            s = ""

                        col_replace = s.replace(' OCTETS', '').replace(
                            '\'0001-01-01-00.00.00.000000\'', '').replace('VARCHAR', 'STRING').replace(
                            'SMALLINT NOT NULL', 'INT NOT NULL').replace(
                            'CHAR', 'STRING').replace('WITH DEFAULT ', '').replace('"', '').strip().replace('0 )',
                                                                                                            ')').strip().replace(
                            '0 ,', ',').replace('COMPRESS YES ADAPTIVE', '').replace('\'TODO\' )', ')').replace(
                            'ORGANIZE BY ROW;', ';').replace('\'0\'', '').replace('\'PEC\'', '').replace('\' \'',
                                                                                                         '').replace(
                            '\'\'', '').replace('\'N\'', '').replace('INTEGER 1 )', 'INT )').replace('0.,',
                                                                                                     ',').replace(
                            '\'YES\'', '').replace('FOR BIT DATA ,', ' ,').replace('CURRENT TIMESTAMP )', ' )').replace(
                            '\'EMAIL.1\' ,', ' ,').replace('INTEGER 1 ,', 'INT ,').replace(
                            'GENERATED BY DEFAULT AS IDENTITY (', ',').replace(
                            'START WITH +1',
                            '').replace(
                            'START WITH +1',
                            '').replace('INCREMENT BY +2',
                                        '').replace('MINVALUE +1',
                                                    '').replace('MAXVALUE +9223372036854775807',
                                                                '').replace('MAXVALUE +999999999',
                                                                            '').replace('NO CYCLE',
                                                                                        '').replace('CACHE 20',
                                                                                                    '').replace(
                            'NO ORDER ) ,',
                            '').replace('00000001',
                                        '').replace('GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1)',
                                                    '').replace('varchar', 'STRING').replace(
                            'timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP NOT NULL').replace(
                            'ON UPDATE CURRENT_TIMESTAMP', '')

                        if len(col_replace.strip()) > 0:
                            new_table += f"\t{col_replace}\n"
                tofile += new_table

            if 'CREATE INDEX' in match.group():
                print(match.group())
                for s in match.group().splitlines():
                    indx = s.replace('CREATE INDEX "' + schema_name + '  "."', 'CREATE INDEX ').replace('  "."',
                                                                                                        '.').replace(
                        'COMPRESS YES',
                        '').replace(
                        'INCLUDE NULL KEYS ALLOW REVERSE SCANS;', '').replace('PCTFREE 10', '').replace('COMPRESS NO',
                                                                                                        '').replace('"',
                                                                                                                    '').replace(
                        'EXCLUDE NULL KEYS ALLOW REVERSE SCANS;', '').replace('COLLECT SAMPLED DETAILED STATISTICS',
                                                                              '').replace('', '')
                    if len(indx.strip()) > 0:
                        tofile += f"\n{indx}"
                tofile += ";\n"

            if 'CREATE UNIQUE INDEX' in match.group():
                for s in match.group().splitlines():
                    indx = s.replace('CREATE UNIQUE INDEX "' + schema_name + '  "."', 'CREATE UNIQUE INDEX ').replace(
                        '  "."',
                        '.').replace(
                        'COMPRESS YES',
                        '').replace(
                        'INCLUDE NULL KEYS ALLOW REVERSE SCANS;', '').replace('PCTFREE 10', '').replace('COMPRESS NO',
                                                                                                        '').replace('"',
                                                                                                                    '').replace(
                        'EXCLUDE NULL KEYS ALLOW REVERSE SCANS;', '').replace('COLLECT SAMPLED DETAILED STATISTICS',
                                                                              '').replace('', '')
                    if len(indx.strip()) > 0:
                        tofile += f"\n{indx}"
                tofile += ";\n\n"

            if 'ALTER TABLE' in match.group() and 'DATA CAPTURE' in dropdown:

                for s in match.group().splitlines():
                    # ALTER TABLE "BCCUST  "."BC_INDIVIDUAL_NAME_HST" DATA CAPTURE CHANGES INCLUDE LONGVAR COLUMNS;
                    dcdreg = r'^(?P<alter>\w+) (?P<table>\w+) \"(?P<schema_name>\w+)  \"\.\"(?P<table_name>\w+)\" DATA CAPTURE CHANGES INCLUDE LONGVAR COLUMNS;'
                    dcdmatches = re.finditer(dcdreg, s, re.MULTILINE)
                    for cdcmatchNum, cdcmatch in enumerate(dcdmatches, start=1):
                        cdcschema = cdcmatch.groupdict()["schema_name"]
                        cdctable = cdcmatch.groupdict()["table_name"]
                        tofile += f"\n-- Create a changefeed & permisisons on table {cdctable}\n"
                        tofile += f"\nGRANT CHANGEFEED ON TABLE {cdctable} TO {cdcuser};\n"
                        sink = f"\nCREATE CHANGEFEED FOR TABLE {cdctable}\n  {cdcoptions}\n"

                        tofile += f"{sink}\n"

            if 'ALTER TABLE' in match.group():
                print(s)
                for s in match.group().splitlines():
                    if 'DATA CAPTURE' not in s:
                        if 'ALTER TABLE ' in s and 'PCTFREE 0;' in s:
                            s = ""
                        if 'ALTER TABLE ' in s and 'RESTART WITH ' in s:
                            tofile += f"-- [seq mod required] {s}"
                        altertable = s.replace('ALTER TABLE "' + schema_name + '  "."',
                                               'ALTER TABLE ' + schema_name + '.').replace('"', '').replace('ENFORCED',
                                                                                                            '').replace(
                            'ENABLE QUERY OPTIMIZATION', '').replace('PCTFREE 0', '')
                        if len(altertable.strip()) > 0:
                            tofile += f"{altertable}\n"
                tofile += "\n"

    # Create a download button
    st.download_button("Download the CockroachDB DDL", tofile, file_name="crdb-" + uploaded_file.name,
                       mime="text/plain")

    st.code(tofile)

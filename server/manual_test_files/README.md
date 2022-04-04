# Help for Manual Test Files

This is a set of files allowing the uploading of a .csv and corresponding .pdf file(s).

You need to be in a 'dataprovider group' to do [http://localhost:5000/upload](http://localhost:5000/upload) or you will see:
```json
Response:
    {
      "message": "Not a member of a data provider group or no group_id provided"
    }
```

Go to [https://app.globus.org/groups](https://app.globus.org/groups).

You need to be added to a group that has 'data provider' capabilities (i.e., the HuBMAP-Testing-Group).
If you are in more than one group you need to specify which one you are going to use.

```json
    {
        "data_provider": true,
        "displayname": "California Institute of Technology TMC",
        "generateuuid": true,
        "name": "hubmap-caltech-tmc",
        "shortname": "TMC - Cal Tech",
        "tmc_prefix": "CALT",
        "uuid": "308f5ffc-ed43-11e8-b56a-0e8017bdda58"
    }
```

## Manual test files to test uploading

You will need to click on the "Add AVRs" link in the top right hand of the search (main) page
to get to the "Antibody Upload" page.
In the section "Antibody Files", click on "Browse..." button, and select the corresponding .csv file.
In the section "Antibody PDFs", click on "Browse..." button, and select the corresponding .pdf file.
Then click on "Submit" button at the bottom of the page.

You will received a screen telling you that validation is taking place while the data in the .csv file
is being verified and the .pdf files validated. If there is a problem, you will received a scree with an
error message telling you on what line there is a problem, and what the problem is. Please fix the problem
and try again. If there is no problem then you will receive a confirmation page telling you that the data
has been uploaded. This enters the antibodies .csv information into the database and also adds it to the
elastic search index so that you can searh for it on the search page.

### Verify in PostgreSQL

The "stable store" for all data is [PostgreSQL](https://www.postgresql.org/).
This section will cover verification that the data has been written to this database.

Consider using [Postico](https://eggerapps.at/postico/).
The connection information is in 'instance/app.conf' at the bottom.
The 'host' should be 'localhost' and not 'db'.
The 'vendors' are normalized in the 'antibodies' table.
The information from the .csv file will be in the 'antibodies'
table with additional timestamp/user/system information.

### Verify in Elastic Search

[Elasticsearch](https://www.elastic.co/) is used for a convenient searching of the data which
which is coppied into Elasticsearch for this purpose. The Search Screen uses Elasticsearch
only. 

You can verify that data has been written to Elasticsearch throught the application.
Go to [http://localhost:5000](http://localhost:5000) and you
should see the information that is available in the database.
You may need to search for specific information.
The 'antibody_name' in the 'antibody' table should match the 'Name' on the webpage.

You can also query Elastic Search directly with
```bash
$ curl -H 'Content-Type: application/json' -X GET http://localhost:9200/hm_antibodies/_search?pretty
```

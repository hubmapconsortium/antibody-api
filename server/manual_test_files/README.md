# Help for Manual Test Files

There are only two scenarios. The first is uploading just a .csv file without a .pdf file.
The second is uploading a .csv and corresponding .pdf file.
It is possible to upload multiple files, and the second scenario below tests that.
If you don't give the .pdf file mentioned in the .csv file, it will be processed in a manner where no .pdf file exists (e.g., it won't give an error).

Need to	be in a	'dataprovider group' to	do [http://localhost:5000/upload](http://localhost:5000/upload) or you will see:
```
Response:
{
  "message": "Not a member of a data provider group or no group_id provided"
}
```

The reason that there is a .csv and .pdf upload is because the .csv file makes reference (optional) to a pdf.

Go to [https://app.globus.org/groups](https://app.globus.org/groups).
You need to be added to a group that has 'data provider' capabilities.
If you are in more than one group you need to specify which one you are going to use.

```
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

## Manual test for 'upload' (.csv only)

You will need to go to [http://localhost:5000/upload](http://localhost:5000/upload) and click on "Choose Files" in "Antibody Files".
Select the './server/manual_test_files/upload/antibodieswithoutpdf.csv' file.
Then click on "Submit". You should see something similar to 'successful_upload.png'.

This will enter the antibodies in the database and also add them to the elastic search index.

### Verify in PostgreSQL

Consider using [Postico](https://eggerapps.at/postico/).
The connection information is in 'instance/app.conf' at the bottom.
The 'host' should be 'localhost' and not 'db'.
The 'vendors' are normalized in the 'antibodies' table.
The information from the .csv file will be in the 'antibodies' table with additional timestamp/user/system information.

### Verify in Elastic Search

This can be done throught the application.
Go to [http://localhost:5000](http://localhost:5000) and you should see the information that is available in the databse.
The 'antibody_name' in the 'antibody' table should match the 'Name' on the webpage.


## Manual test of uploading .csv and .pdf files

Go to [https://app.globus.org/groups](https://app.globus.org/groups).

The data files to use for this are found in 'manual_test_files/upload_multiple_with_pdf'.

It is possible to select multiple files from the interface.
First, click on "Choose Files" in "Antibody Files", you will only be able to see .csv files. Then cmd-click on both antibodies.csv and antibodies2.csv.
Second, click on "Choose Files" in "Antibody PDFs", you will see all files. Then CMD-click on both .pdf files.
Then click 'submit'.

If it succeeds you get back two columns of information: the antibody name, and the unique identifier of the antibodies just uploaded (see uoloadWithPDF.png file).
If you do this multiple times it will make one entry for each upload (it will NOT overwrite).

You can use similar methods to the above to check the database and ElasticSearch.

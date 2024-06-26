# Server

## Configuration

Copy the 'example.app.conf' file to an '/instance/app.conf' (in the root of the repo) file.

Note that values in the '/server/default_config.py' file are overridden by any in the '/instance/app.conf' file.


### Globus

You will need APP_CLIENT_ID, and a APP_CLIENT_SECRET to authenticate (get a bearer token for) the service with Globus.
```commandline
    client = globus_sdk.ConfidentialAppAuthClient(
        app.config['APP_CLIENT_ID'],
        app.config['APP_CLIENT_SECRET']
    )
```

### Servers

You will need to change the '*_ENDPOINT' and '*_API_BASE' urls as needed.

## Running locally

Look at './scripts/README.md'.

## package.json dependencies

To check for new dependencies in package.json use:
```commandline
$ (cd server; npx npm-check-updates)
Checking .../antibody-api/server/package.json
[====================] 20/20 100%

All dependencies match the latest package versions :)
```

to update them to the latest versions use:
```commandline
$ (cd server; npx npm-check-updates -u)
```

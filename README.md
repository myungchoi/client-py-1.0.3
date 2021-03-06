SMART FHIR Client
=================

This is _fhirclient_, a flexible Python client for [FHIR][] servers supporting the [SMART on FHIR][smart] protocol.
The client is compatible with Python 2.7, possibly earlier, and Python 3.

Client versioning is not identical to FHIR versioning.
The `master` branch is usually on the latest version of the client as shown below, possibly on bugfix releases thereof.
See the `develop` branch for models that are closer to the latest FHIR continuous integration builds.

   Version |          FHIR | &nbsp;
-----------|---------------|---
 **1.0.3** |       `1.0.2` | (DSTU 2)
   **1.0** |       `1.0.1` | (DSTU 2)
   **0.5** |  `0.5.0.5149` | (DSTU 2 Ballot, May 2015)
 **0.0.4** | `0.0.82.2943` | (DSTU 1)
 **0.0.3** | `0.0.82.2943` | (DSTU 1)
 **0.0.2** | `0.0.82.2943` | (DSTU 1)


Installation
------------

    pip install fhirclient


Documentation
-------------

Technical documentation is available at [docs.smarthealthit.org/client-py/][docs].

### Client Use

To connect to a SMART on FHIR server (or any open FHIR server), you can use the `FHIRClient` class.
It will initialize and handle a `FHIRServer` instance, your actual handle to the FHIR server you'd like to access.

##### Read Data from Server

To read a given patient from an open FHIR server, you can use:

```python
from fhirclient import client
settings = {
    'app_id': 'my_web_app',
    'api_base': 'https://fhir-open-api-dstu2.smarthealthit.org'
}
smart = client.FHIRClient(settings=settings)

import fhirclient.models.patient as p
patient = p.Patient.read('hca-pat-1', smart.server)
patient.birthDate.isostring
# '1963-06-12'
smart.human_name(patient.name[0])
# 'Christy Ebert'
```

If this is a protected server, you will first have to send your user to the authorize endpoint to log in.
Just call `smart.authorize_url` to obtain the correct URL.
You can use `smart.prepare()`, which will return `False` if the server is protected and you need to authorize.
The `smart.ready` property has the same purpose, it will however not retrieve the server's _Conformance_ statement and hence is only useful as a quick check whether the server instance is ready.

```python
smart = client.FHIRClient(settings=settings)
smart.ready
# prints `False`
smart.prepare()
# prints `True` after fetching Conformance
smart.ready
# prints `True`
smart.prepare()
# prints `True` immediately
smart.authorize_url
# is `None`
```

You can work with the `FHIRServer` class directly, without using `FHIRClient`, but this is not recommended:

```python
smart = server.FHIRServer(None, 'https://fhir-open-api-dstu2.smarthealthit.org')
import fhirclient.models.patient as p
patient = p.Patient.read('hca-pat-1', smart)
patient.name[0].given
# ['Christy']
```

### Data Model Use

The client contains data model classes, built using [fhir-parser][], that handle (de)serialization and allow to work with FHIR data in a Pythonic way.

#### Initialize Data Model

```python
import fhirclient.models.patient as p
import fhirclient.models.humanname as hn
patient = p.Patient({'id': 'patient-1'})
patient.id
# prints `patient-1`

name = hn.HumanName()
name.given = ['Peter']
name.family = ['Parker']
patient.name = [name]
patient.as_json()
# prints patient's JSON representation, now with id and name
```

#### Initialize from JSON file

```python
import json
import fhirclient.models.patient as p
with open('path/to/patient.json', 'r') as h:
    pjs = json.load(h)
patient = p.Patient(pjs)
patient.name[0].given
# prints patient's given name array in the first `name` property
```


### Flask App

Take a look at [`flask_app.py`][flask_app] to see how you can use the client in a simple (Flask) app.
This app starts a webserver, listening on [_localhost:8000_](http://localhost:8000), and prompts you to login to our sandbox server and select a patient.
It then goes on to retrieve the selected patient's demographics and med prescriptions and lists them in a simple HTML page.

The Flask demo app has separate requirements.
Clone the _client-py_ repository, then best create a virtual environment and install the needed packages like so:

    git clone https://github.com/smart-on-fhir/client-py.git
    cd client-py
    virtualenv -p python3 env
    . env/bin/activate
    pip install -r requirements_flask_app.txt
    python flask_app.py


Building Distribution
---------------------

    pip install -r requirements.txt
    python setup.py sdist
    python setup.py bdist_wheel


### Incrementing the lib version

    bumpversion patch
    bumpversion minor
    bumpversion major


Docs Generation
---------------

Docs are generated with [Doxygen][] and [doxypypy][].
You will need to install doxypypy the old-fashioned way, checking out the repo and issuing `python setup.py install`.
Then you can just run Doxygen, configuration is stored in the `Doxyfile`.

Running Doxygen will put the generated documentation into `docs`, the HTML files into `docs/html`.
Those files make up the content of the `gh-pages` branch.
I usually perform a second checkout of the _gh-pages_ branch and copy the html files over, with:

    doxygen
    rsync -a docs/html/ ../client-py-web/


[fhir]: http://www.hl7.org/implement/standards/fhir/
[smart]: http://docs.smarthealthit.org
[fhir-parser]: https://github.com/smart-on-fhir/fhir-parser
[docs]: https://smart-on-fhir.github.io/client-py
[flask_app]: https://github.com/smart-on-fhir/client-py/blob/master/flask_app.py
[doxygen]: http://www.stack.nl/~dimitri/doxygen
[doxypypy]: https://github.com/Feneric/doxypypy

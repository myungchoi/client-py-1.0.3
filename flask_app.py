# -*- coding: utf-8 -*-

import logging
import json
from fhirclient import client
from fhirclient.models.medication import Medication
from fhirclient.models.medicationorder import MedicationOrder
from fhirclient.models.documentreference import DocumentReference
from fhirclient.models.binary import Binary
from base64 import decodestring

from flask import Flask, request, redirect, session
import requests

# app setup
smart_defaults = {
    'app_id': '8157653e-edb9-420c-aeea-24d5f77a4539',
    # 'api_base': 'https://fhir-myrecord.sandboxcerner.com/dstu2/0b8a0111-e8e6-4c26-a91c-5069cbc6b1ca',
    'api_base': 'http://localhost:8080/fhir',
    'redirect_uri': 'http://localhost:8000/fhir-app/',
    # 'scope': 'system/Binary.read system/DocumentReference.read system/Patient.read'
    # 'scope': 'patient/DocumentReference.read patient/Patient.read profile openid'
    'scope': 'patient/DocumentReference.read patient/Patient.read patient/Binary.read user/DocumentReference.read launch profile openid'
}

app = Flask(__name__)
app.secret_key = 'thisistesting'

def _save_state(state):
    session['state'] = state

def _get_smart():
    state = session.get('state')
    if state:
        return client.FHIRClient(state=state, save_func=_save_state)
    else:
        return client.FHIRClient(settings=smart_defaults, save_func=_save_state)

def _logout():
    if 'state' in session:
        smart = _get_smart()
        smart.reset_patient()

def _reset():
    if 'state' in session:
        del session['state']

def _get_prescriptions(smart):
    bundle = MedicationOrder.where({'patient': smart.patient_id}).perform(smart.server)
    pres = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None
    if pres is not None and len(pres) > 0:
        return pres
    return None

def _med_name(prescription):
    if prescription.medicationCodeableConcept and prescription.medicationCodeableConcept.coding[0].display:
        return prescription.medicationCodeableConcept.coding[0].display
    if prescription.text and prescription.text.div:
        return prescription.text.div
    return "Unnamed Medication(TM)"

def _get_documents(smart):
    # if 'server' in session['state']:
    #     server = session['state']['server']
    #     if 'auth' in server:
    #         auth = server['auth']
    #         if 'access_token' in auth:
    #             headers = {'Accept': 'application/json+fhir', 'Authorization': 'Bearer ' + auth['access_token']}
    #         else:
    #             return 'failed to get an access token from auth: {0}'.format(auth)
    #     else:
    #         return 'failed to get a auth from server: {0}'.format(server)
    # else:
    #     return 'failed to get an server: {0}'.format(session['state'])
    #
    # docref_url = '{0}/DocumentReference/$docref?patient={1}&type=http://loinc.org|34133-9'.format(smart.server.base_uri, smart.patient_id)
    # print 'trying to get doc references from {0} with header= {1}'.format(docref_url, headers)
    # r = requests.get(docref_url, timeout=None, headers=headers)
    # if r.status_code is 200:
    #     bundle = r.content
    #     print 'WORKED!!'
    #     return 'WORKED!!'
    #     # docs = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None
    #     # if docs is not None and len(docs) > 0:
    #     #     return docs
    #     # return None
    #     #
    #     # with open('ok_doc.pdf', 'wb') as f:
    #     #     f.write(r.content)
    # else:
    #     print 'failed: {0}'.format(r.status_code)
    #     return 'failed: {0}'.format(r.status_code)

    url = smart_defaults['api_base']+'/DocumentReference/$docref?patient={0}&type=http://loinc.org|34133-9'.format(smart.patient_id)

    print "Getting Document Reference Resources"

    bundle = DocumentReference.where({'patient': smart.patient_id}).perform(smart.server)
    docs = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None

    print "Documents obtained"
    if docs is not None and len(docs) > 0:
        return docs
    return None


def _get_attachment(doc, smart):
    if doc.content and doc.content[0].attachment and doc.content[0].attachment.url:
        url = doc.content[0].attachment.url
        # the last is ID

        print "Document URL: {}".format(url)
        url_components = url.split('/')
        binary_id = url_components[-1]
        filename = "{0}.pdf".format(binary_id)
        print "Trying to save Document Binary to {}".format(filename)
        binary = Binary.read(binary_id, smart.server)
        print "Document read for {}".format(binary_id)
        with open(filename, 'wb') as f:
            f.write(decodestring(binary.content))

        print "Done writing file={}".format(filename)
        return json.dumps(binary.as_json())

        # accept_type = 'application/xml'
        # accept_type = doc.content[0].attachment.contentType
        # if 'server' in session['state']:
        #     server = session['state']['server']
        #     if 'auth' in server:
        #         auth = server['auth']
        #         if 'access_token' in auth:
        #             headers = {'Accept': accept_type, 'Authorization': 'Bearer '+auth['access_token']}
        #         else:
        #             return 'failed to get an access token from auth: {0}'.format(auth)
        #     else:
        #         return 'failed to get a auth from server: {0}'.format(server)
        # else:
        #     return 'failed to get an server: {0}'.format(session['state'])
        #
        # url = smart_defaults['api_base']+'/Binary/$autogen-ccd-if?patient={0}'.format(smart.patient_id)
        # # url = smart_defaults['api_base']+'/DocumentReference/$docref?patient={0}&type=http://loinc.org|34133-9'.format(smart.patient_id)
        #
        # print 'trying to get a PDF document from {0} with header= {1}'.format(url, headers)
        # r = requests.get(url, timeout=None, headers=headers)
        # if r.status_code is 200:
        #     with open('ok_doc.pdf', 'wb') as f:
        #         f.write(r.content)
        # else:
        #     print 'failed: {0}'.format(r.status_code)
        #     return 'failed: {0}'.format(r.status_code)
    else:
        return 'not enough info for attachment'

# views

@app.route('/')
@app.route('/index.html')
def index():
    """ The app's main page.
    """
    smart = _get_smart()
    body = "<h1>Hello</h1>"

    if smart.ready and smart.patient is not None:       # "ready" may be true but the access token may have expired, making smart.patient = None
        name = smart.human_name(smart.patient.name[0] if smart.patient.name and len(smart.patient.name) > 0 else 'Unknown')

        # generate simple body text
        body += "<p>You are authorized and ready to make API requests for <em>{0}</em>.</p>".format(name)
        # body += _get_documents(smart)
        docs = _get_documents(smart)
        if docs is not None and len(docs) > 0:
            # ret = _get_attachment(docs.pop(1), smart)
            # body += "{0}\n".format(ret)
            for doc in docs:
                print "start getting attachment: {0}".format(doc.as_json())
                ret = _get_attachment(doc, smart)
                body += "{0}\n".format(ret)
        else:
            body += "<p>There is no document</p>"

        # pres = _get_prescriptions(smart)
        # if pres is not None:
        #     body += "<p>{0} prescriptions: <ul><li>{1}</li></ul></p>".format("His" if 'male' == smart.patient.gender else "Her", '</li><li>'.join([_med_name(p) for p in pres]))
        # else:
        #     body += "<p>(There are no prescriptions for {0})</p>".format("him" if 'male' == smart.patient.gender else "her")
        body += """<p><a href="/logout">Change patient</a></p>"""
    else:
        auth_url = smart.authorize_url
        if auth_url is not None:
            body += """<p>Please <a href="{0}">authorize</a>.</p>""".format(auth_url)
        else:
            body += """<p>Running against a no-auth server, nothing to demo here. """
        body += """<p><a href="/reset" style="font-size:small;">Reset</a></p>"""
    return body


@app.route('/fhir-app/')
def callback():
    """ OAuth2 callback interception.
    """
    smart = _get_smart()
    try:
        smart.handle_callback(request.url)
    except Exception as e:
        return """<h1>Authorization Error</h1><p>{0}</p><p><a href="/">Start over</a></p>""".format(e)
    return redirect('/')


@app.route('/_launch/')
def _launch():
    api_url = request.args.get('iss')
    launch_id = request.args.get('launch')

    if not api_url.endswith('/'):
        api_url += '/'

    smart_defaults['api_base'] = api_url
    smart_defaults['launch_token'] = launch_id

    print(smart_defaults)

    # We are being launnched. Make sure we reset the state if previous state exists.
    if 'state' in session:
        del session['state']

    # Set up the SMART on FHIR client and handle the launch request.
    smart = _get_smart()

    auth_url = smart.authorize_url
    print('State when started:{0}'.format(session))
    print(auth_url)
    return redirect(auth_url)


@app.route('/launch/')
def launch():
    """ EHR initiated launching url
    """
    body = '<h1>App Testing Launching Page</h1>'
    body += '<p>You are launching from EHR</p>'
    body += '<p><a href="/_launch?launch={0}&iss={1}">Click Here to begin</a></p>'.format(request.args.get('launch'),
                                                                                          request.args.get('iss'))
    body += '<p>iss={0}</p>'.format(request.args.get('iss'))
    body += '<p>launch={0}</p>'.format(request.args.get('launch'))

    return body


@app.route('/logout')
def logout():
    _logout()
    return redirect('/')


@app.route('/reset')
def reset():
    _reset()
    return redirect('/')


# start the app
if '__main__' == __name__:
    import flaskbeaker
    flaskbeaker.FlaskBeaker.setup_app(app)
    
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, port=8000)

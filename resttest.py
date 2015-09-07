from __future__  import print_function
import requests
import json

__author__ = 'massi'

irods_username = 'xtensdevel'
irods_password = 'xtensdevel'
xtens_app_uri = "http://localhost:1337"

irods_rest_uri = "http://130.251.10.60:8080/irods-rest/rest"
file_download_fragm = "/fileContents"
file_info_fragm = "/dataObject"

chunk_size = 1024

def xtens_log_in():
    xtens_credentials = {'identifier':'admin', 'password':'admin1982'}
    # XTENS Requests begin here!!
    r = requests.post(xtens_app_uri + "/login", data=xtens_credentials)
    res = r.json()
    bearer_token = res['token']

    # set headers for bearer auth
    headers = {
        'Authorization': 'Bearer {}'.format(bearer_token),
        'Content-Type': 'application/json'
    }
    return headers


def test_post(data_type_name='MRI'):
    headers = xtens_log_in()

    # get the data type associated to Patient (or another subject type)
    payload = {
        'model': 'Subject',
        'name': 'Patient'
    }
    r = requests.get(xtens_app_uri + '/dataType', headers=headers, params=payload)
    subj_type = r.json()[0]

    subj = {
        'type': subj_type['id'],
        'metadata': {}, # cannot be null, must specify an empty object
        'sex': 'N.D.'
    }

    r = requests.post(xtens_app_uri + '/subject', headers=headers, data=json.dumps(subj))
    created_subject = r.json()
    print(created_subject)

    # retrieve dataType
    payload = {
        'name':'MRI'
    }
    r = requests.get(xtens_app_uri + '/dataType', headers=headers, params=payload)
    id_data_type = r.json()[0]['id']

    # build new data to be created (in thi case an MRI instance with only one metadata field
    payload = {
        'type': id_data_type,
        'parentSubject': created_subject['id'],
        'metadata': {'acquisition_type': {'value':'T1'}}
    }
    r = requests.post(xtens_app_uri + '/data', headers=headers, data=json.dumps(payload))
    created_data = r.json()
    print("New data created: ")
    print(created_data)


def test_get(patient_code, data_type_name):

    #handle authetication (on XTENS). equests to xtens API begin here!!
    headers = xtens_log_in()

    #get patient info
    payload = {'code':patient_code}
    r = requests.get(xtens_app_uri + "/subject", headers=headers, params=payload)
    subject = r.json()[0] # subj CODE is unique so let's take the first element of the lists
    print(subject['id'])

    #get data_type info
    payload = {'name': data_type_name}
    r = requests.get(xtens_app_uri + "/dataType", headers=headers, params=payload)
    data_type = r.json()[0] # data_type NAME is unique so let's take the first element of the lists
    print(data_type['id'])

    id_subject = subject['id']
    id_data_type = data_type['id']

    payload = {
        'parentSubject': id_subject,
        'type': id_data_type
    }

    #make a get to retrieve a data instance
    r = requests.get(xtens_app_uri + "/data", headers=headers, params=payload)

    # get the associated list of files
    data = r.json()

    # for sake of simplicity, let's get the first data instance
    datum = data[1]
    file_list = datum['files']
    print(datum)

    # Requests to irods-rest API begin here!!
    headers = {
        'Accept': 'application/json'
    }

    for data_file in file_list:

        # retrieve file details
        r = requests.get(irods_rest_uri + file_info_fragm + data_file['uri'], headers=headers, auth=(irods_username,irods_password))
        file_detail = r.json()
        print ("File path is: ")
        print(file_detail['dataPath'])


        # retrieve file content and save it on the working directory (with the same file name)
        filename = data_file['uri'].split("/")[-1]
        print("filename is: ", filename)
        with open(filename, 'wb') as fd:
            r = requests.get(irods_rest_uri + file_download_fragm + data_file['uri'], auth=(irods_username,irods_password))

            if not r.ok:
                print("Got some error while trying to download the file")
                r.raise_for_status()

            for chunk in r.iter_content(chunk_size):
                fd.write(chunk)


#   correct address for file download:
#   http://130.251.10.60:8080/irods-rest/rest/dataObject/biolabZone/home/xtensdevel/xtens-repo/MRI/20/The_Sun.jpg
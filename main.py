from flask import Flask, render_template, request



link = "https://sketchfab.com/models/2fb002d8856e48f3bcbe496518cdd06a/embed?autospin=1&autostart=1&ui_hint=0&ui_theme=dark"



#!/usr/bin/python3

"""Sample script for uploading to Sketchfab using the V3 API and the requests library."""

import json
from time import sleep

# import the requests library
# http://docs.python-requests.org/en/latest
# pip install requests
import requests
from requests.exceptions import RequestException

##
# Uploading a model to Sketchfab is a two step process
#
# 1. Upload a model. If the upload is successful, the API will return
#    the model's uid in the `Location` header, and the model will be placed in the processing queue
#
# 2. Poll for the processing status
#    You can use your model id (see 1.) to poll the model processing status
#    The processing status can be one of the following:
#    - PENDING: the model is in the processing queue
#    - PROCESSING: the model is being processed
#    - SUCCESSED: the model has being sucessfully processed and can be view on sketchfab.com
#    - FAILED: the processing has failed. An error message detailing the reason for the failure
#              will be returned with the response
#
# HINTS
# - limit the rate at which you poll for the status (once every few seconds is more than enough)
##

SKETCHFAB_API_URL = 'https://api.sketchfab.com/v3'
API_TOKEN = '0c3cd3c459024c9b914e9f2c5cbfee4b' 
MAX_RETRIES = 50
MAX_ERRORS = 10
RETRY_TIMEOUT = 5  # seconds


def _get_request_payload(*, data=None, files=None, json_payload=False):
    """Helper method that returns the authentication token and proper content type depending on
    whether or not we use JSON payload."""
    data = data or {}
    files = files or {}
    headers = {'Authorization': f'Token {API_TOKEN}'}

    if json_payload:
        headers.update({'Content-Type': 'application/json'})
        data = json.dumps(data)

    return {'data': data, 'files': files, 'headers': headers}



def poll_processing_status(model_url):
    """GET the model endpoint to check the processing status."""
    errors = 0
    retry = 0

    print('Start polling processing status for model')

    while (retry < MAX_RETRIES) and (errors < MAX_ERRORS):
        print(f'Try polling processing status (attempt #{retry})...')

        payload = _get_request_payload()

        try:
            response = requests.get(model_url, **payload)
        except RequestException as exc:
            print(f'Try failed with error {exc}')
            errors += 1
            retry += 1
            continue

        result = response.json()

        if response.status_code != requests.codes.ok:
            print(f'Upload failed with error: {result["error"]}')
            errors += 1
            retry += 1
            continue

        processing_status = result['status']['processing']

        if processing_status == 'PENDING':
            print(f'Your model is in the processing queue. Will retry in {RETRY_TIMEOUT} seconds')
            retry += 1
            sleep(RETRY_TIMEOUT)
            continue
        elif processing_status == 'PROCESSING':
            print(f'Your model is still being processed. Will retry in {RETRY_TIMEOUT} seconds')
            retry += 1
            sleep(RETRY_TIMEOUT)
            continue
        elif processing_status == 'FAILED':
            print(f'Processing failed: {result["error"]}')
            return False
        elif processing_status == 'SUCCEEDED':
            print(f'Processing successful. Check your model here: {model_url}')
            return True

        retry += 1

    print('Stopped polling after too many retries or too many errors')
    return False


def patch_model(model_url):
    """
    PATCH the model endpoint to update its name, description...
    Important: The call uses a JSON payload.
    """

    payload = _get_request_payload(data={'name': 'A super Bob model'}, json_payload=True)

    try:
        response = requests.patch(model_url, **payload)
    except RequestException as exc:
        print(f'An error occured: {exc}')
    else:
        if response.status_code == requests.codes.no_content:
            print('PATCH model successful.')
        else:
            print(f'PATCH model failed with error: {response.content}')


def patch_model_options(model_url):
    """PATCH the model options endpoint to update the model background, shading, orienration."""
    data = {
        'shading': 'shadeless',
        'background': '{"color": "#FFFFFF"}',
        # For axis/angle rotation:
        'orientation': '{"axis": [1, 1, 0], "angle": 34}',
        # Or for 4x4 matrix rotation:
        # 'orientation': '{"matrix": [1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]}'
    }
    payload = _get_request_payload(data=data, json_payload=True)
    try:
        response = requests.patch(f'{model_url}/options', **payload)
    except RequestException as exc:
        print(f'An error occured: {exc}')
    else:
        if response.status_code == requests.codes.no_content:
            print('PATCH options successful.')
        else:
            print(f'PATCH options failed with error: {response.content}')






app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', em_code=link, dis_text='Demo')

@app.route('/upload', methods=['POST','GET'])
def upload():
    if request.method == 'POST':  
        f = request.files['model_file']
        f.save(f.filename)




        model_endpoint = f'{SKETCHFAB_API_URL}/models'

        # Mandatory parameters
        model_file = f.filename  # path to your model

        # Optional parameters
        data = {
            'name': f.filename[:-4],
        }

        print('Uploading...')

        with open(model_file, 'rb') as file_:
            files = {'modelFile': file_}
            payload = _get_request_payload(data=data, files=files)

            try:
                response = requests.post(model_endpoint, **payload)
            except RequestException as exc:
                print(f'An error occured: {exc}')
                return

        if response.status_code != requests.codes.created:
            print(f'Upload failed with error: {response.json()}')
            return

        # Should be https://api.sketchfab.com/v3/models/XXXX
        model_url = response.headers['Location']
        print('Upload successful. Your model is being processed.')
        print(f'Once the processing is done, the model will be available at: {model_url}')
        sleep(80)
        
        code = f'https://sketchfab.com/models/{model_url.split("/")[-1]}/embed?autospin=1&autostart=1&ui_hint=0&ui_theme=dark'
        link = code

        # Process the uploaded file and obtain the necessary parameters for embedding
        # For example, you might extract the model ID or URL from the uploaded file

        # Generate the embed code for the Sketchfab model
        return render_template('index.html', em_code=link, dis_text=f.filename[:-4])

def generate_embed_code(model_id):
    # Use the model ID to generate the embed code for the Sketchfab model
    # You can refer to the Sketchfab API documentation for details on how to generate the embed code
    # Here's a simplified example:
    embed_code = f'<iframe width="100%" height="480px" src="https://sketchfab.com/models/{model_id}/embed"></iframe>'
    return embed_code



if __name__ == '__main__':
    app.run(debug=True)






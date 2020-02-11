from requests_oauthlib import OAuth2Session
import os, time
import traceback

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

CLIENT_ID = 'a31abcfc-d330-4815-a9d0-e15bc871390f'
TOKEN_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
API_URL = 'https://graph.microsoft.com/v1.0'
HEADERS = {
    'SdkVersion': 'nextcloud-backup-1.0',
    'x-client-SKU': 'nextcloud-backup',
    'return-client-request-id': 'true',
    'Content-Type': 'application/json'
}

class OneDrive(object):

    def __init__(self, access_token):
        self.access_token = access_token
        self.session = None

    def get_name(self):
        return 'OneDrive'

    def create_raw_session(self):
        return OAuth2Session(CLIENT_ID, token=self.access_token, scope=self.access_token['scope'])

    def get_session(self):
        token = self.get_token()

        if (not self.session) or self.access_token != token:
            self.session = self.create_raw_session()

        return self.session

    def get_token(self):
        if not self.access_token:
            return

        if (self.access_token['expires_at'] - 300) > time.time():
            return self.access_token

        session = self.create_raw_session()
        self.access_token = session.refresh_token(TOKEN_URL, client_id=CLIENT_ID)
        return self.access_token

    def connect(self):
        self.session = self.get_session()

        if not self.session:
            raise Exception('Could not create OneDrive session.')

        self.root_folders = []
        #self.root_folders = self.get_item_children(self.folder_id)

    def check_error(self, response):
        if 'error' in response:
            error = response['error']
            raise Exception('OneDrive API error: {0} ({1}). Request-ID {2}'.format(error['message'], error['code'], error['innerError']['request-id']))

    def post_api(self, endpoint, data=None):
        if not data:
            data = {}

        response = self.get_session().post(API_URL + endpoint, headers=HEADERS, json=data).json()
        self.check_error(response)
        return response

    def get_api(self, url):
        response = self.get_session().get(url, headers=HEADERS).json()
        self.check_error(response)
        return response

    def get_item_children(self, item_id):
        return self.get_api(API_URL + '/me/drive/items/{0}/children?$top=10000&$select=name,id,size'.format(item_id))['value']

    def create_folder(self, name, folder_id):
        folder = self.post_api('/me/drive/items/{0}/children'.format(folder_id), {'name': name, 'folder': {}})
        return {'name': folder['name'], 'id': folder['id']}

    def create_folder_in_root(self, name):
        folder = self.create_folder(name, self.folder_id)
        self.root_folders.append(folder)
        return folder

    def create_upload_session(self, folder_id, filename):
        request = {'item': {'@microsoft.graph.conflictBehavior': 'replace', 'name': filename}}

        while True:
            try:
                return self.post_api('/me/drive/items/{0}:/{1}:/createUploadSession'.format(folder_id, filename), request)['uploadUrl']
            except:
                print('Could not create upload session, retrying in 3 seconds...')
                traceback.print_exc()
                time.sleep(3)

    def upload_file(self, source_filename, folder_path, filename):
        upload_url = None
        size = os.path.getsize(source_filename)
        complete = False

        while not complete:
            start_byte = 0

            if not upload_url:
                upload_url = self.create_upload_session(folder_path, filename)

            with open(source_filename, 'rb') as f:
                while True:
                    file_content = f.read(10 * 1024 * 1024)
                    data_length = len(file_content)

                    if data_length <= 0:
                        complete = True
                        break

                    end_byte = start_byte + data_length - 1
                    content_range = 'bytes {0}-{1}/{2}'.format(start_byte, end_byte, size)

                    try:
                        chunk_response = self.get_session().put(upload_url, headers={'Content-Length': str(data_length), 'Content-Range': content_range}, data=file_content)
                        status_code = chunk_response.status_code
                    except:
                        chunk_response = None
                        status_code = -1

                    if status_code not in (200, 201, 202):
                        print('Error code {0} during resumable upload of {1} ({2}) ({3})... resuming in 5 seconds.'.format(status_code, source_filename, filename, content_range)) 
                        time.sleep(3)

                        try:
                            self.get_session().delete(upload_url)
                        except:
                            print('Could not delete session {0}...'.format(upload_url))

                        upload_url = None
                        time.sleep(2)
                        break

                    start_byte = end_byte + 1

        return chunk_response

    def list_folders_in(self, folder_id):
        folders = self.get_item_children(folder_id)
        return [folder for folder in folders if 'folder' in folder]

    def list_files_in(self, folder_id):
        folders = self.get_item_children(folder_id)
        return [folder for folder in folders if 'folder' not in folder]

    def search_for_files_by_url(self, results, url):
        result = self.get_api(url)
        results.extend(result['value'])
        nextLink = result.get('@odata.nextLink')

        if nextLink:
            self.search_for_files_by_url(results, nextLink)
    
    def search_for_files_in_root(self, results, filename):
        self.search_for_files_by_url(results, API_URL + "/me/drive/search(q='{0}')".format(filename))

    def search_for_files_in(self, results, folder_id, filename):
        self.search_for_files_by_url(results, API_URL + "/me/drive/items/{0}/search(q='{1}')".format(folder_id, filename))

    def find_file_in_list(self, files, filename):
        for file in files:
            if file['name'] == filename:
                return file

    def find_file_in_root(self, filename):
        return self.find_file_in_list(self.root_folders, filename)
    
    def get_manifests(self):
        folders = {}
        files = []
        self.search_for_files_in_root(files, '*.json')

        for file in files:
            name = file['name']

            if not name.startswith('manifest-'):
                continue

            folder_path = file['parentReference']['path']
            folder_name = file['parentReference']['name']
            folder = folder_path[folder_path.index(':')+1:folder_path.index(folder_name)-1]

            if folder not in folders:
                folders[folder] = []

            folders[folder].append({'name': name, 'link': file['@microsoft.graph.downloadUrl']})

        for folder in folders.keys():
            folders[folder].sort(key=lambda file: file['name'], reverse=True)

        return folders

    def get_file_size(self, file):
        return int(file['size'])

    def get_folder_path(self, folder):
        return folder['id']
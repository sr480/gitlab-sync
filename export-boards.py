import requests
import urllib.parse
import os
from dotenv import load_dotenv
import sys

load_dotenv()

GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITLAB_API_URL = os.getenv('GITLAB_API_URL')

# The IDs of your source and destination projects
source_project_name = sys.argv[1]
destination_project_name = sys.argv[2]

# The IDs of your source and destination boards
source_board_id = '33'
destination_board_id = '48'

# The GitLab API base URL
base_url = GITLAB_API_URL + '/api/v4'

source_project_name_encoded = urllib.parse.quote_plus(source_project_name)
destination_project_name_encoded = urllib.parse.quote_plus(destination_project_name)

# The headers for your requests
headers = {
    'Private-Token': GITLAB_TOKEN
}

# Fetch the lists from the source board
response = requests.get(
    f'{base_url}/projects/{source_project_name_encoded}/lists',
    headers=headers
)
source_lists = response.json()
print(source_lists)
# Create the same lists in the destination board
for list in source_lists:
    label_id = list['label']['id']
    list_name = list['label']['name']
    data = {
        'label_id': label_id
    }
    response = requests.post(
        f'{base_url}/projects/{destination_project_name_encoded}/lists',
        headers=headers,
        json=data
    )
    print(response)
    print(f'Created list "{list_name}" in the destination board.')

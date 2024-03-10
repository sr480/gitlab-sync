## Prepare

Create venv

```
python3 -m venv venv
```
activete env
```
source venv/bin/activate
```

Install deps

```
pip install -r requirements.txt
```

You will need environment file `.env` to configure access to gitlab.

You will need to create `google-access.json` - the instruction is below.

### Sync Issues with google sheets

Run
```
python3 sync.py Backlog 'stdm.web/stdm-user-story'
python3 sync.py Frontend 'stdm.web/stdm-frontend'
python3 sync.py Backend 'stdm.web/stdm-backend'
python3 sync.py ConfigService 'stdm.web/stdm-config-service'
```

Where the first arg is SpreadSheet Sheet's Name, the second is ULR path to the project in Gitlab

### Copy boards from project to project

Copies boards from one project to another

Use the url to boards as arguments

```
python3 export-boards.py 'my-group/source-project/boards/123' 'my-group/destination-project/boards/456'
```

## Environment

```
GITLAB_TOKEN=xxxxxxxxxxxxxxxx
SPREADSHEET_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITLAB_API_URL=https://gitlab.com/
```

## SPREEADSHEET_ID
Use spreadsheet's url to get Id

```
https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit#gid=0
```

## How to get access to gitlab API

Creating an access token in GitLab allows you to authenticate with the GitLab API securely, 
enabling you to manage issues, boards, tags, and more programmatically. 
Follow these steps to create a personal access token in GitLab:

1. Log into your GitLab account: Open your web browser, go to your GitLab instance URL (this could be GitLab.com or a self-hosted instance), and sign in with your credentials.

2. Navigate to Personal Access Tokens settings:

- Click on your profile picture or initials in the upper-right corner of the GitLab interface.
- Select Preferences from the dropdown menu.
- On the left sidebar, under the Access Tokens section, click Access Tokens. This will take you to the personal access tokens page.

3. Create a new Personal Access Token:
In the "Add a personal access token" section, you'll need to provide some details:
- Name: Enter a meaningful name for your token that helps you remember the purpose of the token in the future.
- Expires at: Optionally, you can set an expiration date for the token. After this date, the token will no longer be valid. This is recommended for security purposes.
- Scopes: Select the permissions you want to grant this token. For managing issues, boards, and tags, you will likely need the following scopes:
   - `api`
   - `read_api`
   - `read_user`

4. Generate the token:
- Once you've filled out the form, click the Create personal access token button at the bottom of the page.
- GitLab will generate the token and display it to you. Important: Make sure to copy the token and keep it somewhere safe. You won't be able to see it again once you navigate away from the page or refresh it.

## How to get access to google sheets

!Important! Give access rights to Spread Sheet for the `Service Account`.

To use the Google Sheets API from Python, you need to set up a project in the Google Cloud Console and create credentials which will be saved as a `google-access.json` file. Here are the steps for doing that:

1. **Go to the Google Cloud Console** 

   Visit https://console.cloud.google.com/ and log in with your Google account.

2. **Create a New Project**

   Click on `Select a project` > `New Project`. Name your project and click `Create`.

3. **Enable the Google Sheets API**

   After creating your project, navigate to the Dashboard and click `Enable APIs and Services`.

   Search for `Google Sheets API`, click on it, then click `Enable`.

4. **Create Credentials**

   You're going to create service account keys that will allow you to authenticate your application:
   
   a. Go back to the dashboard and select `APIs & Services > Credentials` from the sidebar.
   
   b. Click `Create Credentials`, then select `Service account`.
   
   c. Fill in details for the Service account. For the Role, you can select `Project` > `Editor`.
   
   d. Click `Done`.

5. **Generate JSON Key File**

   On the `Credentials` page, you'll see a list of all your service accounts. 

   a. Click on the one you just created to go to its details page.
   
   b. Under `Keys` section, click on `Add Key`, select `JSON`.

   This will download a JSON key file (`YOUR-PROJECT-NAME-XXXXXX.json`). This is the `google-access.json` file that you'll use in your Python application to authenticate with the Google Sheets API.

6. **Give service account access to the spreadsheet**

    a. Open your JSON key file and copy the `client_email` value.

    b. Open your Google Spreadsheet and click `Share` button on the right top corner.

    c. Paste the email in the 'People' input field and click `Done`.

Remember to secure your `google-access.json` file properly, as it contains sensitive information that could give someone full access to your Google Sheets if misused.

`google-access.json` file example:

```
{
  "type": "service_account",
  "project_id": "xxxxxxxxxxxxxxxxxxxxxx",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----.......your private key here.......----END PRIVATE KEY-----\n",
  "client_email": "xxxxxxxx@yyyyyyy.google.com",
  "client_id": "12312312312312",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxxxxxxxx.iam.gserviceaccount.com"
}
```

## Export boards

`export-boards.py` allows to copy labels from one gitlab project to other

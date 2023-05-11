# Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './google-access.json'
SPREADSHEET_ID = '1Ex2Po5iTuIHnxne3u2EwaZmQKgjMq9vF9iCbzlDAlW0'
SHEET_NAME = 'BacklogImport'

# GitLab API credentials
GITLAB_TOKEN = 'Xq3iDHRSbmsLR2mPP6p8'
GITLAB_PROJECT_ID = 'stdm.web/stdm-user-story'
GITLAB_API_URL = 'https://gitlab.ugpa.ru/'

import gitlab
import gspread
from google.oauth2 import service_account
from datetime import datetime

# Truncate description to this length
max_desc_len = 400

# Create a GitLab API client instance
gl = gitlab.Gitlab(GITLAB_API_URL, private_token=GITLAB_TOKEN)

# Get the project's issues from GitLab
gl_project = gl.projects.get(GITLAB_PROJECT_ID)
issues = gl_project.issues.list(all=True)

# Create a Google Sheets API client instance
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gs = gspread.authorize(creds)

doc = gs.open_by_key(SPREADSHEET_ID)
sheet_name = SHEET_NAME
try:
  work_sheet = doc.worksheet(sheet_name)
except gspread.exceptions.WorksheetNotFound:
  work_sheet = doc.add_worksheet(sheet_name, rows=100, cols=20)

print(f'Created sheet "{work_sheet.title}"')

work_sheet.clear()

# Get the header row for the sheet
header = ['ID', 'Title', 'Description', 'Created At', 'Updated At', 'Author', 'Assignees', 'Labels', 'State']
work_sheet.append_row(header)

# Add the issues to the sheet
for issue in issues:
  # Truncate the description if necessary
  desc = ''
  if issue.description:
    desc = issue.description[:max_desc_len] if len(issue.description) > max_desc_len else issue.description

  # Create a row for the issue
  row = [
    issue.iid,
    issue.title,
    desc,
    datetime.fromisoformat(issue.created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S'),
    datetime.fromisoformat(issue.updated_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S'),
    issue.author['name'],
    ', '.join(a['name'] for a in issue.assignees),
    ', '.join(l for l in issue.labels),
    issue.state,
  ]

  # Add the row to the sheet
  work_sheet.append_row(row)

print(f'Added {len(issues)} issues to sheet "{doc.title}" in document')

import os
from dotenv import load_dotenv

load_dotenv()

# Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './google-access.json'
SPREADSHEET_ID =os.getenv('SPREADSHEET_ID')

# GitLab API credentials
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITLAB_API_URL = os.getenv('GITLAB_API_URL')

# Truncates thw descirption to this length
MAX_DESC_LEN = 400

# Collects labels from the GitLab issue to Feature type column
FEATURE_TYPES = set(['Epic', 'feature-request', 'bug-report', 'User-story', 'Spec'])

# Collects labels from the GitLab issue to Imact level column
IMPACT_LEVELS = set(['US::Must-have', 'US::Should-have', 'US::Could-have', 'US::Won\'t have',
                'IM::Ultra', 'IM::High', 'IM::Medium', 'IM::Low'
                ])

# Collects labels from the GitLab issue to Confedence column
CONFEDENCE_LEVELS = set(['CF::WellKnown', 'CF::LooksKnown', 'CF::NeedsResearch', 'CF::NoSpec'])

COLUMNS_COUNT = 12
RANGE = 'A2:L'

import gspread
from gspread.worksheet import ValueRange, ValueRenderOption
import gitlab
from gitlab.v4.objects import ProjectIssue
from google.oauth2 import service_account
import sys


worksheet_name = sys.argv[1] # if sys.argv else WORKSHEET
project_name = sys.argv[2] # if sys.argv else GITLAB_PROJECT_ID
    
def import_issue(issue: ProjectIssue, cells):
    desc = issue.description
    issue_type = list(FEATURE_TYPES.intersection(set(issue.labels)))
    issue_impact = list(IMPACT_LEVELS.intersection(set(issue.labels)))
    issue_confedence = list(CONFEDENCE_LEVELS.intersection(set(issue.labels)))
    other_labels = list(set(issue.labels) - IMPACT_LEVELS - FEATURE_TYPES - CONFEDENCE_LEVELS)

    cells[0] = str(issue.iid)
    cells[1] = issue.updated_at
    cells[2] = issue.title
    cells[3] = desc
    cells[4] = issue_type[0] if issue_type else None
    cells[5] = issue_impact[0] if issue_impact else None
    cells[6] = issue_confedence[0] if issue_confedence else None
    cells[7] = ', '.join(other_labels)
    cells[8] = ', '.join(a['name'] for a in issue.assignees)
    cells[9] = issue.author['name']
    cells[10] = issue.state
    cells[11] = issue.milestone['title'] if issue.milestone else None

def export_issue(issue, cells):
    labels = [ cells[4], cells[5], cells[6] ] + cells[7].split(', ')
    labels = [label.strip() for label in labels if label.strip()]
    milestone = None
    if cells[11]:
        milestone = next((m for m in milestones if m.title == cells[11]), None)
    desc = cells[3]

    issue_milestone_id = issue.milestone['id'] if issue.milestone else None
    sheet_milestone_id = milestone.id if milestone else None

    if cells[2] != issue.title or set(labels) != set(issue.labels) or issue_milestone_id != sheet_milestone_id or desc != issue.description:
        issue.title = cells[2]
        issue.labels = labels
        issue.description = desc
        issue.milestone_id = milestone.id if milestone else None
        issue.save()
        return True
    return False

def convertToCellFormat(rows: ValueRange):
    result = []
    columns_count = COLUMNS_COUNT
    for row in rows:
        result_row = [ "" ] * columns_count

        for i in range(min(columns_count, len(row))):
            result_row[i] = row[i]
        result.append(result_row)
    return result


def find_issue(issues, iid):
    for issue in issues:
        if str(issue.iid) == str(iid):
            return issue
    return None

# Set up Google Sheets API credentials
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gs = gspread.authorize(creds)

# Open the specified Google Sheets document
worksheet = gs.open_by_key(SPREADSHEET_ID).worksheet(worksheet_name)

# Set up GitLab API credentials
gl = gitlab.Gitlab(GITLAB_API_URL, private_token=GITLAB_TOKEN)

# Get the existing issues in the specified GitLab project
gl_project = gl.projects.get(project_name)
milestones = gl_project.milestones.list()

issues = gl_project.issues.list(all=True)

count_created = 0
count_exported = 0
count_imported = 0
count_imported_new = 0

empty_row_index = len(worksheet.col_values(1)) + 1
#Reset ID Colors
worksheet.format('A1:A1000', {
    "backgroundColor": {
        "red": 1,
        "green": 1,
        "blue": 1
    }
})

sheet_iids = []

# Fills table header if it's empty
header_row = worksheet.row_values(1)
if len(header_row) < COLUMNS_COUNT:
    header = ['ID', 'Updated At', 'Title', 'Description', 'Feature type', 'Impact level', 'Confedence level', 'Other labels', 'Assignees', 'Author', 'State', 'Milestone']
    worksheet.append_row(header)

# Get all values from the sheet
batch_rows = worksheet.batch_get([RANGE])[0]
rows = convertToCellFormat(worksheet.batch_get([RANGE])[0])

# Loop through each row in the sheet
for row_index, row in enumerate(rows):    
    sheet_iid = row[0]
    sheet_updated_at = row[1]
    sheet_title = row[2]
    # Check if the ID field is empty
    if not sheet_iid and sheet_title:
        # Create a new GitLab issue
        print('creating...')
        labels = [ row[4], row[5], row[6] ] + row[7].split(', ')
        labels = [ label.strip() for label in labels if label.strip() ]
        new_issue = gl_project.issues.create({
            'title': sheet_title,
            'description': row[3],
            'labels': labels
        })
        # Update the ID field in the sheet with the created issue ID
        # Reload saved issue from GL
        gl_reloaded_issue = gl_project.issues.get(new_issue.iid)
        import_issue(gl_reloaded_issue, row)
        worksheet.format('A{0}'.format(row_index + 2), {
            "backgroundColor": {
                "red": 0.7,
                "green": 0.9,
                "blue": 0.7
            }
        })
        count_created += 1

    elif sheet_iid:
        sheet_iids.append(sheet_iid)

        gl_issue = find_issue(issues, int(sheet_iid))
        if gl_issue and sheet_updated_at != gl_issue.updated_at:
            print('importing...')
            import_issue(gl_issue, row)
            worksheet.format('A{0}'.format(row_index + 2), {
                "backgroundColor": {
                    "red": 0.9,
                    "green": 0.9,
                    "blue": 0.7
                }
            })
            count_imported += 1
        elif gl_issue and sheet_updated_at == gl_issue.updated_at:
            if export_issue(gl_issue, row):
              print('exporting...')
              # Reload saved issue from GL
              gl_reloaded_issue = gl_project.issues.get(sheet_iid)
              import_issue(gl_reloaded_issue, row)
              worksheet.format('A{0}'.format(row_index + 2), {
                  "backgroundColor": {
                      "red": 0.7,
                      "green": 0.9,
                      "blue": 0.7
                  }
              })
              count_exported += 1

# Import new issues
new_issues_start = len(rows)
for gl_issue in issues:
    if sheet_iids.count(str(gl_issue.iid)) > 0:
        continue
    row = [ "" ] * COLUMNS_COUNT
    import_issue(gl_issue, row)
    rows.append(row)

    empty_row_index += 1
    count_imported_new += 1
new_issues_end = len(rows)

# Update the cells in batches
cell_list = worksheet.range(RANGE)
row_len = len(rows[0])
for i, cell in enumerate(cell_list):
    row = i // row_len
    col = i % row_len
    try:
        cell.value = rows[row][col]
    except:
        break
worksheet.update_cells(cell_list)

# Set background color for new issues
cells_to_color = 'A{0}:A{1}'.format(new_issues_start + 2, new_issues_end + 2)
print(cells_to_color)
worksheet.format(cells_to_color, {
    "backgroundColor": {
        "red": 0.7,
        "green": 0.9,
        "blue": 0.9
    }
})

print(f'Sync completed, created {count_created}, exported {count_exported}, imported {count_imported}, imported new {count_imported_new} issues')
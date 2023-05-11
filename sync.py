# Google Sheets API credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './google-access.json'
SPREADSHEET_ID = '1Ex2Po5iTuIHnxne3u2EwaZmQKgjMq9vF9iCbzlDAlW0'

# GitLab API credentials
GITLAB_TOKEN = 'Xq3iDHRSbmsLR2mPP6p8'
GITLAB_PROJECT_ID = 'stdm.web/stdm-user-story'
GITLAB_API_URL = 'https://gitlab.ugpa.ru/'

MAX_DESC_LEN = 400
FEATURE_TYPES = set(['Epic', 'feature-request', 'bug-report', 'User-story'])
IMPACT_LEVELS = set(['US::Must-have', 'US::Should-have', 'US::Could-have', 'US::Won\'t have',
                'IM::Ultra', 'IM::High', 'IM::Medium', 'IM::Low'
                ])
CONFEDENCE_LEVELS = set(['CF::WellKnown', 'CF::LooksKnown', 'CF::NeedsResearch', 'CF::NoSpec'])

import gspread
import gitlab
from gitlab.v4.objects import ProjectIssue
from google.oauth2 import service_account
import sys

worksheet_name = sys.argv[1] # if sys.argv else WORKSHEET
project_name = sys.argv[2] # if sys.argv else GITLAB_PROJECT_ID

def import_issue(issue: ProjectIssue, cells):
    desc = ''
    if issue.description:
      desc = issue.description[:MAX_DESC_LEN] if len(issue.description) > MAX_DESC_LEN else issue.description
    issue_type = list(FEATURE_TYPES.intersection(set(issue.labels)))
    issue_impact = list(IMPACT_LEVELS.intersection(set(issue.labels)))
    issue_confedence = list(CONFEDENCE_LEVELS.intersection(set(issue.labels)))
    other_labels = list(set(issue.labels) - IMPACT_LEVELS - FEATURE_TYPES - CONFEDENCE_LEVELS)

    cells[0].value = issue.iid
    cells[1].value = issue.updated_at
    cells[2].value = issue.title
    cells[3].value = desc
    cells[4].value = issue_type[0] if issue_type else None
    cells[5].value = issue_impact[0] if issue_impact else None
    cells[6].value = issue_confedence[0] if issue_confedence else None
    cells[7].value = ', '.join(other_labels)
    cells[8].value = ', '.join(a['name'] for a in issue.assignees)
    cells[9].value = issue.author['name']
    cells[10].value = issue.state
    cells[11].value = issue.milestone['title'] if issue.milestone else None

def export_issue(issue, cells):
    labels = [ cells[4].value, cells[5].value, cells[6].value ] + cells[7].value.split(', ')
    labels = [label.strip() for label in labels if label.strip()]
    milestone = None
    if cells[11].value:
        milestone = next((m for m in milestones if m.title == cells[11].value), None)

    issue_milestone_id = issue.milestone['id'] if issue.milestone else None
    sheet_milestone_id = milestone.id if milestone else None

    if cells[2].value != issue.title or set(labels) != set(issue.labels) or issue_milestone_id != sheet_milestone_id:
        issue.title = cells[2].value
        issue.labels = labels
        issue.milestone_id = milestone.id if milestone else None
        issue.save()
        return True
    return False


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
worksheet.format('A{0}:A{1}'.format(1, empty_row_index), {
    "backgroundColor": {
        "red": 1,
        "green": 1,
        "blue": 1
    }
})

sheet_iids = []
# Loop through each row in the sheet
for row_index, row in enumerate(worksheet.get_all_values()):    
    # Skip the header row
    if row_index == 0:
        continue

    sheet_iid = row[0]
    sheet_updated_at = row[1]
    sheet_title = row[2]
    
    # Check if the ID field is empty
    if not sheet_iid and sheet_title:
        # Create a new GitLab issue
        print('creating...')
        labels = [ row[4], row[5], row[6] ] + row[7].split(', ')
        labels = [label.strip() for label in labels if label.strip()]
        new_issue = gl_project.issues.create({
            'title': row[2],
            'description': row[3],
            'labels': labels
        })
        # Update the ID field in the sheet with the created issue ID
        # Reload saved issue from GL
        gl_reloaded_issue = gl_project.issues.get(new_issue.iid)
        cells = worksheet.range('A{0}:L{0}'.format(row_index + 1))
        import_issue(gl_reloaded_issue, cells)
        worksheet.update_cells(cells)
        worksheet.format('A{0}'.format(row_index + 1), {
            "backgroundColor": {
                "red": 0.7,
                "green": 0.9,
                "blue": 0.7
            }
        })
        count_created += 1

    elif sheet_iid:
        sheet_iids.append(sheet_iid)

        gl_issue = find_issue(issues, sheet_iid)
        if gl_issue and sheet_updated_at != gl_issue.updated_at:
            print('importing...')
            cells = worksheet.range('A{0}:L{0}'.format(row_index + 1))
            import_issue(gl_issue, cells)
            worksheet.update_cells(cells)
            worksheet.format('A{0}'.format(row_index + 1), {
                "backgroundColor": {
                    "red": 0.9,
                    "green": 0.9,
                    "blue": 0.7
                }
            })
            count_imported += 1
        elif gl_issue and sheet_updated_at == gl_issue.updated_at:
            cells = worksheet.range('A{0}:L{0}'.format(row_index + 1))
            if export_issue(gl_issue, cells):
              print('exporting...')
              # Reload saved issue from GL
              gl_reloaded_issue = gl_project.issues.get(sheet_iid)
              import_issue(gl_reloaded_issue, cells)
              worksheet.update_cells(cells)
              worksheet.format('A{0}'.format(row_index + 1), {
                  "backgroundColor": {
                      "red": 0.7,
                      "green": 0.9,
                      "blue": 0.7
                  }
              })
              count_exported += 1


for gl_issue in issues:
    if sheet_iids.count(str(gl_issue.iid)) > 0:
        continue
    cells = worksheet.range('A{0}:L{0}'.format(empty_row_index))
    import_issue(gl_issue, cells)
    worksheet.update_cells(cells)
    worksheet.format('A{0}'.format(empty_row_index), {
        "backgroundColor": {
            "red": 0.7,
            "green": 0.9,
            "blue": 0.9
        }
    })
    empty_row_index += 1
    count_imported_new += 1

print(f'Sync completed, created {count_created}, exported {count_exported}, imported {count_imported}, imported new {count_imported_new} issues')
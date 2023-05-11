## Prepare

Create venv

```
python3 -m venv venv
source venv/bin/activate
```

Install deps

```
pip install google-auth gspread python-gitlab
```

Run
```
python3 sync.py Backlog 'stdm.web/stdm-user-story'
python3 sync.py Frontend 'stdm.web/stdm-frontend'
python3 sync.py Backend 'stdm.web/stdm-backend'
```


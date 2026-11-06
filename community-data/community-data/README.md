# Community data

The spreadsheet in `data/` is the single source of truth for the community directory.
A script turns it into JSON files that the directory page, a website, or other tools can read.

```
community-data/
├── data/
│   └── Communities_List.xlsx        <- edit this (the only file people touch)
├── public/
│   ├── communities.json             <- generated: one card per community (used by the directory page)
│   └── communities-flat.json        <- generated: one record per spreadsheet row (for other tools)
├── scripts/
│   └── build_communities.py         <- spreadsheet -> JSON
├── .github/workflows/
│   └── build-data.yml               <- runs the script automatically when the spreadsheet changes
└── requirements.txt
```

## Updating the data
1. On GitHub, open `data/`, choose **Add file > Upload files**, and upload the new spreadsheet.
   Keep the file name `Communities_List.xlsx` so it replaces the old one.
2. Commit to `main`. The **Build community data** action runs, regenerates `public/`, and commits the result.
3. The commit history shows who changed what and when. To undo a bad upload, revert the commit.

If the action fails, open the **Actions** tab. Errors (missing columns, no rows) stop the build.
Warnings (unit totals that don't add up, odd addresses, codes with stray spaces) are printed in the log and don't block it.

## Running it on your computer
```
pip install -r requirements.txt
python scripts/build_communities.py
```

## Notes
- Required columns: Community Code, Community, Phone Number, Site Type, Address, Units Total, plus the 13 amenity columns.
- Rows that share a Community Code are combined into one card (like Jefferson main and east).
- Cleanup rules live in the script: Disability % shows as a percentage ("None"/"N/A" become "No"),
  utilities wording is standardized, and apostrophes in names are made typographic.
- Reading from a **private** repo: the browser can't fetch the files directly. Use a small serverless function
  (for example on Vercel) that reads the file with a GitHub token kept in an environment variable.
- If branch protection blocks pushes to `main`, allow the GitHub Actions bot to push, or have the action open a pull request instead.

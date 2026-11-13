# Community data

The spreadsheet in `data/` is the single source of truth for the community directory.
A script turns it into JSON files that the directory page, a website, or other tools can read.

```
community-data/
├── data/
│   └── Communities_List.xlsx        <- edit this (the only file people touch)
├── public/
│   ├── index.html                   <- the directory page (loads communities.json)
│   ├── communities.json             <- generated: one card per community (used by the directory page)
│   └── communities-flat.json        <- generated: one record per spreadsheet row (for other tools)
├── vercel.json                      <- tells Vercel to serve the public/ folder
├── scripts/
│   ├── build_communities.py         <- spreadsheet -> JSON
│   └── requirements.txt             <- Python packages for the script
└── .github/workflows/
    └── build-data.yml               <- runs the script automatically when the spreadsheet changes
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
pip install -r scripts/requirements.txt
python scripts/build_communities.py
```

## Notes
- Everything in `public/` is served publicly by Vercel, including `communities.json`. Only put data here that anyone may see.
- Required columns: Community Code, Community, Phone Number, Site Type, Address, Units Total, plus the 13 amenity columns.
- Rows that share a Community Code are combined into one card (like Jefferson main and east).
- Cleanup rules live in the script: Disability % shows as a percentage ("None"/"N/A" become "No"),
  utilities wording is standardized, and apostrophes in names are made typographic.
- If branch protection blocks pushes to `main`, allow the GitHub Actions bot to push, or have the action open a pull request instead.

## Hosting on Vercel
1. Import this repo into Vercel.
2. Framework Preset: **Other**. Leave the build command empty and set the Output Directory to `public` (vercel.json already says this).
3. After each spreadsheet upload, the GitHub Action commits new JSON, and Vercel redeploys automatically.
   The directory page is at `/`, and other sites or tools can read `/communities.json` and `/communities-flat.json`.
4. Don't put a `requirements.txt` or `pyproject.toml` in the repo root: Vercel would treat the repo as a Python app.

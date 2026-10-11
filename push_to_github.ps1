# Run from inside the LAWTRACE folder in PowerShell, after creating an EMPTY repo named LAWTRACE on github.com.
# Usage:  .\push_to_github.ps1 -User your-github-username
param([Parameter(Mandatory = $true)][string]$User)
if (-not (Test-Path .git)) { git init -b main }
git add -A
git commit -m "LAWTRACE: legal study assistant for Indian law" 2>$null
git remote remove origin 2>$null
git remote add origin "https://github.com/$User/LAWTRACE.git"
git push -u origin main
Write-Host "Pushed. Now deploy at https://share.streamlit.io (main file: app.py)"

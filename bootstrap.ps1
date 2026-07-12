# bootstrap.ps1 — enable the SalesIntel_AI git workflow for THIS clone.
# Run once from the repo root:  .\bootstrap.ps1
# Sets the shared hooks (block direct pushes to main + auto co-author) and the
# required commit identity. See .claude/skills/git-workflow for the full workflow.
git config core.hooksPath .githooks
git config user.name  "indrani-projects"
git config user.email "indrani.patra.projects@gmail.com"
Write-Host "SalesIntel git workflow enabled for this clone:" -ForegroundColor Green
Write-Host "  core.hooksPath = $(git config core.hooksPath)"
Write-Host "  identity       = $(git config user.name) <$(git config user.email)>"
Write-Host "Reminder: never commit or push to 'main' directly — branch -> PR only." -ForegroundColor Yellow

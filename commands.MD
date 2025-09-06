Run hooks on all files (manually):

pre-commit run --all-files


Update all hooks to latest versions:

pre-commit autoupdate


Temporarily skip hooks (not recommended, but sometimes needed):

git commit -m "msg" --no-verify

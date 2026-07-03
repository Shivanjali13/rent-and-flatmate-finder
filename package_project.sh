# Remove previous ZIP (if it exists)
rm -f /d/outputs/rent-flatmate-finder-day2.zip

# Go to the parent directory of the project
cd /d

# Create a clean ZIP archive
zip -r -q /d/outputs/rent-flatmate-finder-day2.zip rent-flatmate-finder \
-x "*.git*" \
-x "*__pycache__*" \
-x "*.db" \
-x "*node_modules*" \
-x "*dist*" \
-x "*package-lock.json*" \
-x "*.pyc" \
-x ".env" \
-x "venv/*" \
-x ".venv/*" \
-x ".pytest_cache/*"

echo "=== FINAL TREE ==="

# Show project files
cd /d/rent-flatmate-finder

find . -type f \
-not -path "./.git/*" \
-not -path "*__pycache__*" \
-not -path "*node_modules*" \
-not -path "*dist*" \
-not -path "*venv/*" \
-not -path "*.venv/*" \
-not -name "*.pyc" \
-not -name "*.db" \
-not -name ".env" \
| sort
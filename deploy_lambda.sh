#!/bin/bash
set -e

echo "=== Building Lambda Package ==="
cd /Users/ben.conlon/projects/poolie/lambda

# Create package directory
rm -rf package
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t ./package --quiet

# Copy app code
cp app.py ./package/

# Create zip
cd package
zip -r ../lambda.zip . > /dev/null
cd ..

echo "=== Lambda zip created: lambda.zip ==="

# Run Terraform deploy
echo "=== Running Terraform ==="
cd ../terraform/environments/dev
terraform init -input=false
terraform apply -auto-approve -input=false

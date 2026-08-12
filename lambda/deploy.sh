#!/bin/bash
set -e

# Build Lambda package
cd $(dirname $0)
pip install -r requirements.txt -t ./package
cp app.py ./package/
cd package
zip -r ../lambda.zip .
cd ..

# Deploy with Terraform
cd ../terraform/environments/dev
terraform init
terraform apply -var-file="terraform.tfvars"

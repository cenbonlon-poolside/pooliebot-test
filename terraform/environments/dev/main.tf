terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "discord" {
  source = "../../modules/discord"
  
  app_id                   = var.discord_app_id
  interaction_endpoint_url   = module.aws.lambda_url
}

module "aws" {
  source = "../../modules/aws"
  
  poolside_api_key  = var.poolside_api_key
  discord_public_key = var.discord_public_key
  discord_app_id    = var.discord_app_id
  lambda_zip_path   = "../../lambda.zip"
}

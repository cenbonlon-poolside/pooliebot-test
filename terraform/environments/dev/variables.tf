variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "poolside_api_key" {
  description = "Poolside API key"
  type        = string
  sensitive   = true
}

variable "discord_public_key" {
  description = "Discord application public key"
  type        = string
}

variable "discord_app_id" {
  description = "Discord application ID"
  type        = string
}

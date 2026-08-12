variable "app_id" {
  type = string
}

variable "interaction_endpoint_url" {
  type = string
}

output "app_id" {
  value = var.app_id
}

output "registration_url" {
  value = "https://discord.com/developers/applications/${var.app_id}/bot"
}

variable "poolside_api_key" {
  type = string
}

variable "discord_public_key" {
  type = string
}

variable "discord_app_id" {
  type = string
}

variable "lambda_zip_path" {
  type = string
  default = "../lambda.zip"

data "aws_caller_identity" "current" {}

# Lambda function
resource "aws_lambda_function" "poolie_bot" {
  function_name    = "poolie-discord-bot"
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  role             = aws_iam_role.lambda.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      POOLSIDE_API_KEY    = var.poolside_api_key
      DISCORD_PUBLIC_KEY  = var.discord_public_key
      LOG_LEVEL           = "INFO"
    }
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda" {
  name = "poolie-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda.name
}

# API Gateway
resource "aws_apigatewayv2_api" "discord" {
  name          = "poolie-discord-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.discord.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.discord.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.poolie_bot.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.discord.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.poolie_bot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.discord.execution_arn}/*/*"
}

output "lambda_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "lambda_name" {
  value = aws_lambda_function.poolie_bot.function_name
}

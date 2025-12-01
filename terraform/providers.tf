terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Always pin versions in production!
    }
  }
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = var.aws_region
  # It will automatically use the credentials you set up in 'aws configure'
}

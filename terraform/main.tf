terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.0.0"
    }
  }
}

#aws keys configured in the local with aws cli to avoid hard coding 
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "demo-bucket" {
  bucket = "sample-bucket-quasi"

  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}

resource "random_password" "rdft-password" {
  length           = 16
  special          = true
  override_special = "!@#$%^&*()-_/[]"

}

resource "random_string" "random-suffix" {
  length  = 6
  special = false

}

resource "aws_redshift_cluster" "ny-taxi-cluster" {
  cluster_identifier = "tf-redshift-cluster"
  database_name      = "nytaxi"
  master_username    = "nytaxiwarehouse"
  master_password    = random_password.rdft-password.result
  node_type          = "ra3.large"
  cluster_type       = "single-node"
  
  skip_final_snapshot = true
}

resource "aws_secretsmanager_secret" "redshift_connection_creds" {
  description = "Redshift connect creds"
  name        = "redshift_secret_${random_string.random-suffix.result}"
}

resource "aws_secretsmanager_secret_version" "redshift_connection" {
  secret_id = aws_secretsmanager_secret.redshift_connection_creds.id
  secret_string = jsonencode({
    username            = aws_redshift_cluster.ny-taxi-cluster.master_username
    password            = random_password.rdft-password.result
    engine              = "redshift"
    host                = aws_redshift_cluster.ny-taxi-cluster.endpoint
    port                = "5439"
    dbClusterIdentifier = aws_redshift_cluster.ny-taxi-cluster.cluster_identifier
  })

}
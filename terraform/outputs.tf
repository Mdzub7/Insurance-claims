output "dynamodb_table_name" {
  value = aws_dynamodb_table.claims_table.name
}


# Add output components for all services

#output "s3_bucket_name" {
#  value = aws_s3_bucket.claims_docs.id
#}

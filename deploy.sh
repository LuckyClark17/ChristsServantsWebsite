set -e

cd Backend

echo "Building and Deploying Network Stack"
sam build -t network-template.yaml && sam deploy --stack-name cs-network-stack --no-confirm-changeset --no-fail-on-empty-changeset

echo "Building and Deploying IAM Stack"
sam build -t iam-template.yaml && sam deploy --stack-name cs-iam-stack --no-confirm-changeset --no-fail-on-empty-changeset

echo "Building and Deploying Data Stack"
sam build -t data-template.yaml && sam deploy --stack-name cs-data-stack --no-confirm-changeset --no-fail-on-empty-changeset

echo "Building and Deploying API Stack"
sam build -t api-template.yaml && sam deploy --stack-name cs-api-stack --no-confirm-changeset --no-fail-on-empty-changeset

echo "Re-Deploying Frontend:"
aws amplify start-job --app-id d1y0l8029swz9t --branch-name main --job-type RELEASE

echo "All tasks dispatched succesfully"
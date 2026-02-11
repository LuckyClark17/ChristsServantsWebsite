set -e

cd Backend

echo "Building and Deploying SAM"
sam build && sam deploy

echo "Re-Deploying Frontend:"
aws amplify start-job --app-id d1y0l8029swz9t --branch-name main --job-type RELEASE

echo "All tasks dispatched succesfully"
# Authenticate
gcloud auth login

# Set your project ID (must be globally unique)
PROJECT_ID="ridehome-poc"

# Create the project
gcloud projects create $PROJECT_ID \
  --name="Ride Home Migration PoC" \
  --set-as-default

# Verify it was created
gcloud projects describe $PROJECT_ID

# Set as active project
gcloud config set project $PROJECT_ID

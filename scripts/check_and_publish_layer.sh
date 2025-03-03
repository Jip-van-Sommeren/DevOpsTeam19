#!/bin/bash
set -e

LAYER_NAME="db_layer"
LAYER_ZIP="db_layer.zip"
RUNTIME="python3.13"

# Calculate the local zip file's SHA256 hash in hexadecimal format.
LOCAL_HASH_HEX=$(sha256sum "$LAYER_ZIP" | awk '{print $1}')
# Convert the hexadecimal hash to base64.
LOCAL_HASH_BASE64=$(echo "$LOCAL_HASH_HEX" | xxd -r -p | base64)
echo "Local layer hash (base64): $LOCAL_HASH_BASE64"

# Get the latest deployed layer version for LAYER_NAME.
LATEST_VERSION=$(aws lambda list-layer-versions --layer-name "$LAYER_NAME" --query 'LayerVersions[0].Version' --output text 2>/dev/null || echo "None")

if [ "$LATEST_VERSION" == "None" ]; then
  echo "No deployed layer versions found. A new version will be published."
  PUBLISH=true
else
  # Retrieve the deployed layer's CodeSha256.
  DEPLOYED_HASH=$(aws lambda get-layer-version --layer-name "$LAYER_NAME" --version-number "$LATEST_VERSION" --query 'Content.CodeSha256' --output text)
  echo "Deployed layer hash (version $LATEST_VERSION): $DEPLOYED_HASH"

  if [ "$LOCAL_HASH_BASE64" == "$DEPLOYED_HASH" ]; then
    echo "Layer content has not changed. Skipping publishing a new version."
    PUBLISH=false
  else
    echo "Layer content has changed. Proceeding to publish a new version."
    PUBLISH=true
  fi
fi

if [ "$PUBLISH" = true ]; then
  aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --zip-file fileb://"$LAYER_ZIP" \
    --compatible-runtimes "$RUNTIME"
  echo "New layer version published."
fi

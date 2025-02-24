# In scripts/check_update.sh
check_update() {
  local FUNCTION_NAME=$1
  echo "Checking update status for $FUNCTION_NAME..."
  while true; do
    STATUS=$(aws lambda get-function-configuration --function-name "$FUNCTION_NAME" | jq -r '.LastUpdateStatus')
    if [ "$STATUS" = "Successful" ]; then
      echo "$FUNCTION_NAME update completed."
      break
    elif [ "$STATUS" = "InProgress" ]; then
      echo "$FUNCTION_NAME is still updating. Waiting..."
      sleep 5
    else
      echo "Unexpected status ($STATUS) for $FUNCTION_NAME. Exiting."
      exit 1
    fi
  done
}

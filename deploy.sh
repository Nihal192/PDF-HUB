#!/bin/bash
# PDF-HUB Deployment Script
# Usage: ./deploy.sh <build_number> <server> <deploy_user>

set -e

BUILD_NUMBER=${1:-latest}
DEPLOY_HOST=${2:-localhost}
DEPLOY_USER=${3:-appuser}
DEPLOY_PATH="/opt/pdf-hub"
APP_PORT="5000"
SSH_KEY="$HOME/.ssh/id_rsa"

echo "📦 Deploying pdf-hub build #$BUILD_NUMBER to $DEPLOY_HOST..."

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found at $SSH_KEY"
    exit 1
fi

# 1. Stop running application
echo "🛑 Stopping current application..."
ssh -i "$SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
    "cd $DEPLOY_PATH && pkill -f 'python app.py' || true" || true

# 2. Create deployment directory
echo "📁 Creating deployment directory..."
ssh -i "$SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
    "mkdir -p $DEPLOY_PATH/build && cd $DEPLOY_PATH"

# 3. Deploy artifact
echo "📤 Uploading build artifact..."
scp -i "$SSH_KEY" -r build/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/build-$BUILD_NUMBER"

# 4. Backup previous version
echo "💾 Backing up previous version..."
ssh -i "$SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
    "cd $DEPLOY_PATH && [ -d current ] && mv current previous-$(date +%s) || true"

# 5. Link to new version
echo "🔗 Activating new version..."
ssh -i "$SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
    "cd $DEPLOY_PATH && ln -sfn build-$BUILD_NUMBER current"

# 6. Install dependencies and start
echo "🚀 Starting application..."
ssh -i "$SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
    "cd $DEPLOY_PATH/current && \
     python3 -m venv venv && \
     source venv/bin/activate && \
     pip install -q -r requirements.txt && \
     nohup python app.py > app.log 2>&1 &"

# 7. Wait for app to start
echo "⏳ Waiting for application to start..."
sleep 5

# 8. Health check
echo "🏥 Running health check..."
if ssh -i "$SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" \
    "curl -s http://localhost:$APP_PORT/ > /dev/null && echo '✓ Health check passed'"; then
    echo "✅ Deployment successful!"
    exit 0
else
    echo "❌ Health check failed!"
    exit 1
fi

# Jenkins CI/CD Setup Guide (Docker-Free)

## Prerequisites

### Jenkins Server
- Jenkins 2.361+
- Installed plugins:
  - Pipeline
  - Git
  - GitHub
  - SSH (SSH Agent plugin)

### Target Deployment Server
- Python 3.10+
- SSH access enabled
- User with deployment permissions (e.g., `appuser`)

---

## 1. Configure Jenkins Credentials

### Add SSH Key Credentials
1. Go to **Jenkins Dashboard** → **Manage Jenkins** → **Credentials**
2. Click **System** → **Global credentials**
3. Click **Add Credentials**
   - Kind: **SSH Username with private key**
   - ID: `deploy-ssh-key`
   - Username: `appuser` (or your deployment user)
   - Private Key: Paste your SSH private key
   - Passphrase: (if applicable)
4. Click **Create**

### Add GitHub Webhook (Optional)
1. Go to your GitHub repo → **Settings** → **Webhooks**
2. Click **Add webhook**
   - Payload URL: `http://jenkins-server:8080/github-webhook/`
   - Content type: `application/json`
   - Events: `Push events`
   - Active: ✓

---

## 2. Create Jenkins Pipeline Job

### Create New Job
1. **New Item** → Name: `pdf-hub-pipeline` → **Pipeline** → **OK**

### Configure Job
1. **Build Triggers**: Check `GitHub hook trigger for GITScm polling`
2. **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/YOUR-ORG/pdf-hub.git`
   - Credentials: Select your GitHub credentials
   - Branches to build: `*/main`

3. Click **Save**

---

## 3. Configure Environment Variables in Jenkinsfile

Update these in your Jenkinsfile or Jenkins job:

```groovy
environment {
    DEPLOY_HOST = 'your-server.com'      // Your target server
    DEPLOY_USER = credentials('deploy-ssh-key')
    DEPLOY_PATH = '/opt/pdf-hub'          // Where to deploy
    APP_PORT = '5000'
}
```

---

## 4. Setup on Target Server

### Create Deployment Directory
```bash
sudo mkdir -p /opt/pdf-hub
sudo chown appuser:appuser /opt/pdf-hub
sudo chmod 755 /opt/pdf-hub
```

### Generate SSH Keys (if needed)
```bash
# On Jenkins server
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Copy public key to deployment server
ssh-copy-id -i ~/.ssh/id_rsa.pub appuser@your-server.com
```

### Install Python & Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip
```

### Setup Systemd Service (Optional for auto-restart)
```bash
sudo cp systemd-pdf-hub.service /etc/systemd/system/pdf-hub.service
sudo systemctl daemon-reload
sudo systemctl enable pdf-hub.service
```

---

## 5. First Deployment

### Option A: Using deploy.sh Script
```bash
./deploy.sh <build-number> <server> <deploy-user>
# Example:
./deploy.sh 1 my-server.com appuser
```

### Option B: Manual Trigger
1. Go to Jenkins **Dashboard** → **pdf-hub-pipeline**
2. Click **Build Now**
3. Watch build logs in **Console Output**

---

## 6. Monitor Deployment

### Check Application Status
```bash
ssh appuser@your-server.com
cd /opt/pdf-hub/current
source venv/bin/activate
tail -f app.log
```

### Check Process
```bash
ps aux | grep "python app.py"
curl http://localhost:5000/
```

---

## 7. Rollback (if needed)

```bash
ssh appuser@your-server.com
cd /opt/pdf-hub
pkill -f "python app.py"
[ -d previous ] && ln -sfn previous current
./current/venv/bin/python ./current/app.py &
```

---

## Troubleshooting

### SSH Connection Failed
- Check SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
- Verify server SSH access: `ssh -v appuser@server.com`

### Application won't start
- Check venv activation: `source /opt/pdf-hub/current/venv/bin/activate`
- Check dependencies: `pip list`
- Check Flask port: `lsof -i :5000`

### Health check fails
- Check if Flask is listening: `netstat -tuln | grep 5000`
- Check app logs: `tail -f /opt/pdf-hub/current/app.log`

---

## Security Best Practices

- [ ] Use SSH keys instead of passwords
- [ ] Limit deployment user permissions
- [ ] Use firewall rules to restrict port 5000
- [ ] Enable Jenkins SSL/TLS
- [ ] Store sensitive credentials in Jenkins Credentials
- [ ] Use a load balancer/reverse proxy (Nginx) in production

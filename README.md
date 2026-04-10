# PDF-HUB

A simple Flask-based PDF utility app for converting, splitting, and merging PDFs.

## Jenkins CI/CD Pipeline

A `Jenkinsfile` is included in the repository to build and validate the application.

### Pipeline behavior

- `Checkout` - checks out the repository from SCM
- `Install dependencies` - installs Python dependencies from `requirements.txt`
- `Validate` - runs `python -m py_compile app.py`
- `Build Docker image` - builds the Docker image using `Dockerfile`
- `Publish Docker image` - pushes the image when `DOCKER_REGISTRY` is set
- `Deploy (optional)` - runs `docker-compose up -d --build` when `DEPLOY_WITH_DOCKER_COMPOSE=true`

### Jenkins job setup

1. Create a new Pipeline job in Jenkins.
2. Point the job to this repository.
3. Configure the job to use the `Jenkinsfile` from source control.
4. Add build environment variables if needed:
   - `DOCKER_REGISTRY` - optional Docker registry host/path
   - `DEPLOY_WITH_DOCKER_COMPOSE=true` - optional local deployment after build

### GitHub push trigger

The Jenkinsfile includes `githubPush()`, so Jenkins can be triggered by GitHub repository push events.
If you use GitHub, configure a webhook in repository settings:
- Payload URL: `http://<JENKINS_HOST>/github-webhook/`
- Content type: `application/json`
- Trigger on: `Push` events

In Jenkins, enable the GitHub plugin or the GitHub webhook trigger for the pipeline job.

### Manual approval on main

When the pipeline runs on the `main` branch, it will stop at the `Approval` stage and wait for a user to accept or deny deployment in the Jenkins UI.
This lets you review the pipeline phases before the optional deploy stage executes.

### Docker image naming

The image name is set to `pdf-hub` and the tag is based on the Jenkins build number.
If `DOCKER_REGISTRY` is provided, the pipeline pushes to the configured registry.

### Running locally

```bash
python -m pip install -r requirements.txt
python app.py
```

### Requirements

- Python
- Docker
- Docker Compose
- Jenkins with Docker access

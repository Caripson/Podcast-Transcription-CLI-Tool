# Production Setup Guide

Follow these step‑by‑step recipes to deploy the Podcast Transcription CLI Tool in production on Local Linux, AWS EC2, AWS Serverless (Transcribe), or containers (ECS/Fargate). Each path is designed to be reliable, repeatable, and secure.

Related:
- Orchestrator configuration keys and examples: [Orchestrator Config](orchestrator-config.md)
- Whisper language parameters: [Whisper Languages](whisper-languages.md)

⚠️ Prerequisites

- Python 3.9+ and `python3-venv` available
- Choose your backend:
  - 🧠 Local Whisper: needs `ffmpeg` and the `openai-whisper` Python package
  - ☁️ AWS Transcribe: IAM access + S3 bucket (`AWS_TRANSCRIBE_S3_BUCKET`)
  - 🔈 GCP Speech: `GOOGLE_APPLICATION_CREDENTIALS`
- Keep secrets in an environment file you do NOT commit (e.g., `.env`).

—

## A) Local Linux Server (systemd)

1️⃣ Install system packages

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg python3-venv
```

2️⃣ Create an app user and folders

```bash
sudo useradd -m -r -s /bin/bash podx || true
sudo mkdir -p /opt/podcast-transcriber /var/lib/podcast-transcriber/cache /var/log/podcast-transcriber
sudo chown -R podx:podx /opt/podcast-transcriber /var/lib/podcast-transcriber /var/log/podcast-transcriber
```

3️⃣ Deploy code and install dependencies

```bash
sudo -u podx bash -lc '
  cd /opt/podcast-transcriber && \
  python3 -m venv .venv && \
  . .venv/bin/activate && \
  pip install -U pip && \
  pip install -e . && \
  pip install openai-whisper  # if using --service whisper
'
```

4️⃣ Add config and environment

- Config: `/opt/podcast-transcriber/config.yml` (for the orchestrator)
- Env file: `/opt/podcast-transcriber/.env`

Example `.env`:

```
AWS_TRANSCRIBE_S3_BUCKET=my-transcribe-bucket
# GOOGLE_APPLICATION_CREDENTIALS=/opt/podcast-transcriber/gcp.json
```

5️⃣ Create a systemd service

Create `/etc/systemd/system/podcast-transcriber.service`:

```
[Unit]
Description=Podcast Transcriber Orchestrator
After=network.target

[Service]
User=podx
WorkingDirectory=/opt/podcast-transcriber
EnvironmentFile=-/opt/podcast-transcriber/.env
ExecStart=/opt/podcast-transcriber/.venv/bin/podcast-cli run --config /opt/podcast-transcriber/config.yml
# Or a single run example:
# ExecStart=/opt/podcast-transcriber/.venv/bin/podcast-transcriber --url https://example.com/episode.mp3 --service whisper --language en --output /var/lib/podcast-transcriber/out.txt
Restart=on-failure
StandardOutput=append:/var/log/podcast-transcriber/service.log
StandardError=append:/var/log/podcast-transcriber/service.err

[Install]
WantedBy=multi-user.target
```

Optional timer `/etc/systemd/system/podcast-transcriber.timer`:

```
[Unit]
Description=Run Podcast Transcriber periodically

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

6️⃣ Start and verify

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now podcast-transcriber.service
# Or enable the timer instead
sudo systemctl enable --now podcast-transcriber.timer
```

🧪 Test a one‑off run

```bash
sudo -u podx /opt/podcast-transcriber/.venv/bin/podcast-transcriber \
  --url <URL|path> --service whisper --language en --output /var/lib/podcast-transcriber/out.txt
```

—

## B) AWS EC2 (managed host)

1️⃣ Prepare AWS resources

- Create/choose an S3 bucket, e.g., `my-transcribe-bucket`.
- Create an IAM role for EC2 with:
  - Transcribe: `StartTranscriptionJob`, `GetTranscriptionJob`, `ListTranscriptionJobs`
  - S3: `PutObject`, `GetObject`, `ListBucket` for the bucket(s)

2️⃣ Launch EC2

- AMI: Ubuntu 22.04 (or Amazon Linux)
- Instance profile: the IAM role above
- Storage: add space for cache and outputs
- Security group: restrict inbound (SSH only is typical)

3️⃣ Configure the instance

SSH in and follow the Local Linux steps (install packages, create venv, add `.env`, create systemd service). Set a cache directory if using Whisper:

```bash
sudo mkdir -p /mnt/podcast-cache
# Then add --cache-dir /mnt/podcast-cache to your config or CLI
```

4️⃣ Validate

```bash
podcast-transcriber --url <URL|path> --service aws \
  --auto-language --aws-language-options sv-SE,en-US --output out.txt
```

—

## C) AWS Serverless (S3 → Lambda → AWS Transcribe)

Goal: Fully managed, event‑driven pipeline. Use AWS Transcribe via the CLI’s `--service aws` inside a Lambda container image.

1️⃣ Build a Lambda image

Dockerfile (save as `lambda.Dockerfile`):

```Dockerfile
FROM public.ecr.aws/lambda/python:3.12
WORKDIR /var/task
COPY . /var/task
RUN python -m pip install --upgrade pip \
 && python -m pip install -e . \
 && python -m pip install awscli

# Handler
COPY lambda_function.py ./
CMD ["lambda_function.handler"]
```

Handler (save as `lambda_function.py`):

```python
import os, subprocess

def handler(event, context):
    rec = event["Records"][0]
    bucket = rec["s3"]["bucket"]["name"]
    key = rec["s3"]["object"]["key"]
    media = f"s3://{bucket}/{key}"

    out_path = "/tmp/out.txt"
    cmd = [
        "podcast-transcriber", "--url", media, "--service", "aws",
        "--auto-language", "--output", out_path,
    ]
    subprocess.run(cmd, check=True)

    out_bucket = os.environ.get("OUTPUT_BUCKET", bucket)
    out_key = key.rsplit(".", 1)[0] + ".txt"
    subprocess.run(["aws", "s3", "cp", out_path, f"s3://{out_bucket}/{out_key}", "--acl", "private"], check=True)
    return {"ok": True, "output": f"s3://{out_bucket}/{out_key}"}
```

2️⃣ Push the image to ECR

```bash
aws ecr create-repository --repository-name podcast-transcriber-lambda || true
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/podcast-transcriber-lambda"
aws ecr get-login-password | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
docker build -t podcast-lambda -f lambda.Dockerfile .
docker tag podcast-lambda:latest "$REPO:latest"
docker push "$REPO:latest"
```

3️⃣ Create a Lambda function

- Runtime: Container image → your ECR image
- Memory: 1024 MB+ recommended
- Timeout: 5–15 minutes depending on media length
- Role permissions: S3 read/write + Transcribe `Start/Get`
- Env vars: `OUTPUT_BUCKET` (optional)

4️⃣ Add an S3 trigger

- Source bucket: where you upload audio
- Event: `PUT` (Object Created)

5️⃣ Test 🧪

Upload an audio file to the source bucket. Expect a transcript in the `OUTPUT_BUCKET` (or the same bucket) with `.txt` suffix.

ℹ️ Notes

- Do not use Whisper in Lambda (too large/slow). Use `--service aws`.
- For advanced orchestration, use Step Functions (start → wait → fetch → publish).

—

## D) Containers on ECS/Fargate (optional)

1️⃣ Build and push an image

```bash
docker build -t podcast-transcriber:base -f Dockerfile .
aws ecr create-repository --repository-name podcast-transcriber || true
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
REPO="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/podcast-transcriber"
aws ecr get-login-password | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
docker tag podcast-transcriber:base "$REPO:latest"
docker push "$REPO:latest"
```

2️⃣ Create a Task Definition

- Command: `podcast-cli run --config /etc/podcast-transcriber/config.yml`
- Env: set `.env` values as Task env vars or from Secrets Manager
- Volumes: optional writable volume for cache/models (Whisper) and outputs
- Task role: S3 + Transcribe permissions as needed

3️⃣ Run as a Service or Scheduled Task

- Service: long‑running orchestrator
- Scheduled task: EventBridge rule (e.g., hourly)

—

## Example Orchestrator config.yml

Minimal Whisper (local) 📄

```yaml
# config.yml
service: whisper            # whisper | aws | gcp
quality: standard           # quick | standard | premium
language: null              # auto-detect; or e.g., en, sv, es
output_dir: ./out           # where artifacts are written

# Write Markdown by default when no outputs are defined
emit_markdown: true
# markdown_template: src/podcast_transcriber/templates/ebook.md.j2

feeds:
  - name: MyShow
    url: https://example.com/podcast/feed.xml

# Optional explicit outputs (remove emit_markdown if you use these)
outputs:
  - { fmt: epub }
  - { fmt: md, md_include_cover: true }
  - { fmt: txt }
  # PDF example with a Unicode font
  - fmt: pdf
    pdf_font_file: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```

Minimal AWS Transcribe ☁️

```yaml
service: aws
quality: standard           # affects downstream processing only
language: null              # use --auto-language via CLI if desired
output_dir: ./out

feeds:
  - name: MyShow
    url: https://example.com/podcast/feed.xml

outputs:
  - { fmt: txt }
  - { fmt: epub }
```

Run it

```bash
podcast-cli run --config config.yml
```

—

## Operations & Tips

🔧 Configuration

- Pass a config with `--config config.yml`. Common defaults: `author`, `language`, `format`, `title`, output paths, `--cache-dir`.

🧰 Whisper models & cache

- Mount persistent storage or set a shared cache (`--cache-dir`) to avoid re‑downloading models.

🖨️ PDF fonts

- Use a Unicode TTF/OTF (e.g., DejaVu) via `--pdf-font-file` for full character coverage.

📈 Monitoring

- Linux: `systemctl status` and logs in `/var/log/podcast-transcriber`.
- AWS: CloudWatch Logs for ECS/Lambda and EC2 via the CloudWatch Agent.

🔐 Security

- Prefer IAM roles over long‑term keys. Never commit `.env`. Scope S3 permissions to specific buckets.

—

## Quick Commands

```bash
# Orchestrator (beta)
podcast-cli run --config config.yml

# One-off transcription
podcast-transcriber --url <URL|path> --service whisper --language en --output out.txt
podcast-transcriber --url <URL|path> --service aws --auto-language --output out.txt
```

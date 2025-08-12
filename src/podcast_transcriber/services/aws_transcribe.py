import os
import time
import uuid
from typing import Optional

import requests

from .base import TranscriptionService


class AWSTranscribeService(TranscriptionService):
    """Minimal AWS Transcribe integration using S3 + polling.

    Requirements:
    - boto3 installed
    - AWS credentials configured
    - Env var AWS_TRANSCRIBE_S3_BUCKET set to an accessible bucket
    - Optional: AWS_REGION (defaults to us-east-1)
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        identify_language: bool = False,
        language_options: Optional[list[str]] = None,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._identify_language = identify_language
        self._language_options = language_options or []

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        try:
            import boto3  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "AWS Transcribe requires 'boto3'. Install with: pip install boto3"
            ) from e

        bucket = self._bucket or os.environ.get("AWS_TRANSCRIBE_S3_BUCKET")
        if not bucket:
            raise RuntimeError(
                "Set AWS_TRANSCRIBE_S3_BUCKET to an S3 bucket for AWS Transcribe input/output."
            )
        region = self._region or os.environ.get("AWS_REGION", "us-east-1")

        s3 = boto3.client("s3", region_name=region)
        transcribe = boto3.client("transcribe", region_name=region)

        key = f"transcribe-input/{uuid.uuid4().hex}{os.path.splitext(audio_path)[1]}"
        s3.upload_file(audio_path, bucket, key)

        job_name = f"job-{uuid.uuid4().hex}"
        media_uri = f"s3://{bucket}/{key}"
        start_kwargs = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": media_uri},
        }
        if language:
            start_kwargs["LanguageCode"] = language
        elif self._identify_language:
            start_kwargs["IdentifyLanguage"] = True
            if self._language_options:
                start_kwargs["LanguageOptions"] = self._language_options
        else:
            start_kwargs["LanguageCode"] = "en-US"
        transcribe.start_transcription_job(**start_kwargs)

        # Poll for completion
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job = status["TranscriptionJob"]
            state = job["TranscriptionJobStatus"]
            if state == "COMPLETED":
                uri = job["Transcript"]["TranscriptFileUri"]
                resp = requests.get(uri, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                # AWS format: {"results": {"transcripts": [{"transcript": "..."}]}}
                transcripts = data.get("results", {}).get("transcripts", [])
                text = " ".join(t.get("transcript", "") for t in transcripts).strip()
                return text
            if state == "FAILED":
                reason = job.get("FailureReason", "Unknown error")
                raise RuntimeError(f"AWS Transcribe failed: {reason}")
            time.sleep(5)

import os
import time
import uuid
from typing import Optional, List, Dict

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
        keep: bool = False,
        speakers: Optional[int] = None,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._identify_language = identify_language
        self._language_options = language_options or []
        self._keep = keep
        self._speakers = speakers
        self.last_segments: List[Dict] = []
        self.last_words: List[Dict] = []

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
        # Speaker diarization settings if requested
        settings = {}
        if self._speakers and self._speakers > 0:
            settings["ShowSpeakerLabels"] = True
            settings["MaxSpeakerLabels"] = int(self._speakers)
        if settings:
            start_kwargs["Settings"] = settings

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
                # AWS format: {"results": {"transcripts": [...], "items": [...], "speaker_labels": {...}}}
                results = data.get("results", {})
                transcripts = results.get("transcripts", [])
                text = " ".join(t.get("transcript", "") for t in transcripts).strip()
                # Parse word-level and diarized segments if present
                items = results.get("items", []) or []
                words: List[Dict] = []
                for it in items:
                    if it.get("type") == "pronunciation":
                        alt = (it.get("alternatives") or [{}])[0]
                        words.append({
                            "start": float(it.get("start_time", 0.0)),
                            "end": float(it.get("end_time", 0.0)),
                            "word": alt.get("content", ""),
                        })
                spk_map: Dict[float, str] = {}
                labels = (results.get("speaker_labels") or {}).get("segments", []) or []
                for seg in labels:
                    spk = seg.get("speaker_label")
                    for li in seg.get("items", []) or []:
                        st = li.get("start_time")
                        if st is not None:
                            try:
                                spk_map[float(st)] = spk
                            except Exception:
                                pass
                segments: List[Dict] = []
                # Group consecutive words by same speaker label
                cur: List[Dict] = []
                cur_spk: Optional[str] = None
                for w in words:
                    spk = spk_map.get(w.get("start"))
                    if spk != cur_spk and cur:
                        segments.append({
                            "start": cur[0]["start"],
                            "end": cur[-1]["end"],
                            "text": " ".join(x.get("word", "") for x in cur).strip(),
                            "speaker": cur_spk,
                        })
                        cur = []
                    cur.append(w)
                    cur_spk = spk
                if cur:
                    segments.append({
                        "start": cur[0]["start"],
                        "end": cur[-1]["end"],
                        "text": " ".join(x.get("word", "") for x in cur).strip(),
                        "speaker": cur_spk,
                    })
                self.last_words = words
                self.last_segments = segments
                # Attempt to delete input object unless keeping
                if not self._keep:
                    try:
                        s3.delete_object(Bucket=bucket, Key=key)
                    except Exception:
                        pass
                return text
            if state == "FAILED":
                reason = job.get("FailureReason", "Unknown error")
                # Cleanup object on failure as well unless keeping
                if not self._keep:
                    try:
                        s3.delete_object(Bucket=bucket, Key=key)
                    except Exception:
                        pass
                raise RuntimeError(f"AWS Transcribe failed: {reason}")
            time.sleep(5)

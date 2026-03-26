from __future__ import annotations

import json
import logging
import os

import boto3

from soccer_analytics.config import Settings


logger = logging.getLogger(__name__)


class RawSnapshotStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    def put_json(self, key: str, payload: dict) -> None:
        if not self.settings.s3_bucket:
            return
        if not os.getenv("AWS_ACCESS_KEY_ID") and self.settings.app_env == "local":
            logger.info("Skipping S3 upload in local mode without AWS credentials.")
            return

        body = json.dumps(payload, default=str).encode("utf-8")
        try:
            if self._client is None:
                self._client = boto3.client("s3", region_name=self.settings.aws_region)
            self._client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Unable to write raw snapshot to S3: %s", exc)

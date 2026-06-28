"""Point the Function Compute 3.0 function at a new container image.

Called by CI after the image is pushed, so every commit auto-deploys to FC
by its immutable per-commit digest — no manual console step, and no stale
`:latest` digest pinning.

This is a *partial* UpdateFunction: only `customContainerConfig.image` is
sent, so the function's environment variables, timeout, port, etc. are left
exactly as configured in the console.

Required env vars (set as GitHub Actions secrets / vars):
  ALIBABA_FC_ACCESS_KEY_ID      RAM key id with fc:UpdateFunction permission
  ALIBABA_FC_ACCESS_KEY_SECRET  RAM key secret
  FC_ACCOUNT_ID                 Alibaba Cloud account id (e.g. 5129681027390288)
  FC_REGION                     e.g. ap-southeast-1
  FC_FUNCTION_NAME              e.g. claimfarm-api
  FC_IMAGE                      full image ref to deploy, e.g.
                                ghcr.io/hemnaath04/claimfarm:<sha>

If the key/account secrets are absent the script exits 0 (no-op) so builds
don't fail before the secrets are configured.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    ak = os.environ.get("ALIBABA_FC_ACCESS_KEY_ID", "").strip()
    sk = os.environ.get("ALIBABA_FC_ACCESS_KEY_SECRET", "").strip()
    account_id = os.environ.get("FC_ACCOUNT_ID", "").strip()
    region = os.environ.get("FC_REGION", "ap-southeast-1").strip()
    function_name = os.environ.get("FC_FUNCTION_NAME", "claimfarm-api").strip()
    image = os.environ.get("FC_IMAGE", "").strip()

    if not (ak and sk and account_id and image):
        # Report which inputs are present (booleans only — never values) so a
        # secret-vs-variable mix-up is obvious from the CI log.
        print(
            "fc_update_image: skipping FC auto-deploy — some inputs are empty. "
            "Presence: "
            f"ACCESS_KEY_ID={bool(ak)} ACCESS_KEY_SECRET={bool(sk)} "
            f"FC_ACCOUNT_ID={bool(account_id)} FC_IMAGE={bool(image)}. "
            "AK id/secret must be repository *Secrets*; FC_ACCOUNT_ID may be a "
            "*Variable* or *Secret*."
        )
        return 0

    # Imported lazily so the no-op path needs no SDK installed.
    from alibabacloud_fc20230330 import models as fc_models
    from alibabacloud_fc20230330.client import Client as FCClient
    from alibabacloud_tea_openapi import models as open_api_models

    endpoint = f"{account_id}.{region}.fc.aliyuncs.com"
    config = open_api_models.Config(
        access_key_id=ak,
        access_key_secret=sk,
        endpoint=endpoint,
        read_timeout=30000,
        connect_timeout=30000,
    )
    client = FCClient(config)

    body = fc_models.UpdateFunctionInput(
        custom_container_config=fc_models.CustomContainerConfig(image=image)
    )
    request = fc_models.UpdateFunctionRequest(body=body)

    print(f"fc_update_image: updating {function_name} ({endpoint}) → {image}")
    resp = client.update_function(function_name, request)
    deployed = getattr(resp.body, "custom_container_config", None)
    print("fc_update_image: done. image now:", getattr(deployed, "image", "?"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"fc_update_image: FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)

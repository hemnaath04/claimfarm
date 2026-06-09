# Proof of Alibaba Cloud Deployment

> This document satisfies the hackathon's hard requirement: "Demonstrate that the backend is running on Alibaba Cloud."

## Code references

The following files demonstrate use of Alibaba Cloud SDKs and APIs. Links will be filled in once each module lands:

- **Alibaba OSS** (object storage for photos and generated claim PDFs): `app/clients/alibaba_oss.py`
- **Alibaba DashVector** (vector database for RAG): `app/clients/dashvector_client.py`
- **Alibaba Function Compute** (serverless deploy target): `deploy/function_compute.yml` (or equivalent), to be added in Task #11.

## Deployment evidence

To be added in Task #11:

- Screenshot of the Alibaba Cloud console showing the deployed Function Compute service.
- Screenshot of the OSS bucket with uploaded files.
- Screenshot of DashVector with indexed collections.
- A short screen recording (linked here) showing a live request hitting the Alibaba-hosted endpoint.

from google.cloud import storage, exceptions

import base64
import json
import os
import re


def copy_badge(bucket_name, obj, new_obj):
    client = storage.Client()

    try:
        bucket = client.get_bucket(bucket_name)
    except exceptions.NotFound:
        raise RuntimeError(f"Could not find bucket {bucket_name}")
    else:
        blob = bucket.get_blob(obj)
        if blob is None:
            raise RuntimeError(f"Could not find object {obj} in bucket {bucket_name}")
        else:
            bucket.copy_blob(blob, bucket, new_name=new_obj)


def build_badge(event, context):
    """
    Background Cloud Function to be triggered by Pub/Sub.

    Updates repository build badge. Triggered by incoming
    pubsub messages from Google Cloud Build.
    """

    decoded = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(decoded)

    try:
        repo = data['source']['repoSource']['repoName']

        if repo.startswith('github_') or repo.startswith('bitbucket_'):
            # mirrored repo format: (github|bitbucket)_<owner>_<repo>
            repo = repo.split('_', 2)[-1]
    except KeyError:
        # github app
        repo = data['substitutions']['REPO_NAME']
    finally:
        src = 'badges/{}.svg'.format(data['status'].lower())
        dest = 'builds/{}.svg'.format(repo)

        bucket = os.environ['BADGES_BUCKET']

        copy_badge(bucket, src, dest)

        return

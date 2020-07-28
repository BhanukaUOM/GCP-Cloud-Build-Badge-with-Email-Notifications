from google.cloud import storage, exceptions

import base64
import json
import os
import re
from string import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def copy_badge(bucket_name, obj, new_obj):
    print(f'Copying Badge {obj} -> {new_obj} to {bucket_name}')
    client = storage.Client()

    try:
        bucket = client.get_bucket(bucket_name)
    except exceptions.NotFound:
        raise RuntimeError(f"Could not find bucket {bucket_name}")
    else:
        blob = bucket.get_blob(obj)
        if blob is None:
            raise RuntimeError(
                f"Could not find object {obj} in bucket {bucket_name}")
        else:
            bucket.copy_blob(blob, bucket, new_name=new_obj)


def send_email(repo, branch, build_status):
    print(f'Sending Email Repo {repo}/{branch}. Build Status {build_status}')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDER_EMAIL_ADDRESS = os.environ.get('SENDER_EMAIL_ADDRESS')
    RECEIVER_EMAIL_ADDRESS = os.environ.get('RECEIVER_EMAIL_ADDRESS')

    message = Mail(
        from_email=SENDER_EMAIL_ADDRESS,
        to_emails=RECEIVER_EMAIL_ADDRESS,
        subject=f'Cloud Build - {repo} ({branch})',
        html_content=f'<h1>Cloud Build - {repo} ({branch})</h1><br/><strong>{build_status}</strong>')
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
        raise e


def build_badge(event, context, is_test=False):
    print('Function build_badge Execution Started')
    """
    Background Cloud Function to be triggered by Pub/Sub.

    Updates repository build badge. Triggered by incoming
    pubsub messages from Google Cloud Build.
    """

    decoded = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(decoded)

    bucket = os.environ['BADGES_BUCKET']

    try:
        repo = data['source']['repoSource']['repoName']
        branch = data['source']['repoSource']['branchName']

        if repo.startswith('github_') or repo.startswith('bitbucket_'):
            # mirrored repo format: (github|bitbucket)_<owner>_<repo>
            repo = repo.split('_', 2)[-1]
    except KeyError:
        # github app
        repo = data['substitutions']['REPO_NAME']
        branch = data['substitutions']['BRANCH_NAME']
    finally:
        build_status = data['status'].lower()
        tmpl = os.environ.get('TEMPLATE_PATH', 'builds/${repo}/branches/${branch}.svg')

        src = f'badges/{build_status}.svg'
        dest = Template(tmpl).substitute(repo=repo, branch=branch)

        copy_badge(bucket, src, dest)
        if not is_test and build_status in ['failure', 'cancelled', 'internal_error', 'timeout']:
            send_email(repo, branch, build_status)
        return

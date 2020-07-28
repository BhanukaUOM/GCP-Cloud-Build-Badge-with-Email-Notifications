import os
import argparse

parser = argparse.ArgumentParser(description='GCP Cloud Build Badge with Email Notifications')
parser.add_argument('--google_cloud_project', required=True, help='GOOGLE CLOUD PROJECT ID')
parser.add_argument('--sendgrid_api_key', required=True, help='SENDGRID API KEY')
parser.add_argument('--sender_email_address', required=True, help='Notification SENDER EMAIL ADDRESS')
parser.add_argument('--receiver_email_address', required=True, help='Notification RECEIVER EMAIL ADDRESS')

args = parser.parse_args()
GOOGLE_CLOUD_PROJECT = args.google_cloud_project
SENDGRID_API_KEY = args.sendgrid_api_key
SENDER_EMAIL_ADDRESS = args.sender_email_address
RECEIVER_EMAIL_ADDRESS = args.receiver_email_address

os.system(f'gsutil mb gs://{GOOGLE_CLOUD_PROJECT}-badges/')
os.system(f'gsutil defacl ch -u AllUsers:R gs://{GOOGLE_CLOUD_PROJECT}-badges/')
os.system(f'gsutil -m -h "Cache-Control:no-cache,max-age=0" cp ./badges/*.svg gs://{GOOGLE_CLOUD_PROJECT}-badges/badges/')
os.system(f'gcloud iam service-accounts create cloud-build-badge')
os.system(f'gsutil iam ch serviceAccount:cloud-build-badge@{GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com:legacyObjectReader,legacyBucketWriter gs://{GOOGLE_CLOUD_PROJECT}-badges/')
os.system("gcloud functions deploy cloud-build-badge --source . --runtime python37 --entry-point build_badge --service-account cloud-build-badge@{}.iam.gserviceaccount.com --trigger-topic=cloud-builds --set-env-vars BADGES_BUCKET={},TEMPLATE_PATH='{}',SENDGRID_API_KEY={},SENDER_EMAIL_ADDRESS={},RECEIVER_EMAIL_ADDRESS={}".format(GOOGLE_CLOUD_PROJECT, f'{GOOGLE_CLOUD_PROJECT}-badges', 'builds/${repo}/branches/${branch}.svg', SENDGRID_API_KEY, SENDER_EMAIL_ADDRESS, RECEIVER_EMAIL_ADDRESS))

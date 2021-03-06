import requests
import boto3
from random import random
from django.core.management.base import BaseCommand
from django.db.models import Q
from botocore.exceptions import ClientError
from user.models import User
from django.conf import settings
import logging


AWS_REGION = 'us-east-1'
client = boto3.client('s3', region_name=AWS_REGION)
logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Script to get user data from github - should run daily'

    def handle(self, *args, **options):
        try:
            users = User.objects.all().exclude(
                Q(github=''), Q(profileDirectoryHash='')
            )

            for user in users:
                image_r = None

                if user.profileDirectoryHash:
                    location = 'https://ipfs.infura.io/ipfs/{}/{}'.format(user.profileDirectoryHash, user.profileFileName)
                    image_r = requests.get(location)

                elif user.github and not user.profile_touched_manually and not user.profile_image:
                    github_username = user.github
                    if not github_username:
                        continue
                    url = 'https://api.github.com/users/{}'.format(github_username)
                    r = requests.get(
                        url, headers={
                            'Authorization': 'token ' + settings.GITHUB_TOKEN})

                    if r.status_code == 200:
                        github_data = r.json()
                        github_image = github_data.get('avatar_url')
                        image_r = requests.get(github_image)

                if image_r and image_r.status_code == 200:
                    try:
                        nonce = int(random() * 1000)
                        bucket = 'assets.bounties.network'
                        key = '{}/userimages/{}-{}.jpg'.format(
                            settings.ENVIRONMENT, user.public_address, nonce)

                        client.put_object(
                            Body=image_r.content,
                            ContentType=image_r.headers['content-type'],
                            Bucket=bucket,
                            ACL='public-read',
                            Key=key)

                        user.profile_image = 'https://{}/{}'.format(bucket, key)
                        user.is_profile_image_dirty = False
                        user.save()

                        logger.info('uploaded for: {}'.format(user.public_address))
                    except ClientError as e:
                        logger.error(e.response['Error']['Message'])

        except Exception as e:
            # goes to rollbar
            logger.exception(e)
            raise e

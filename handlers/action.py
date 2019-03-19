'''<HANDLER DESCRIPTION>'''

import json
import logging
import os
import shutil

import boto3 as boto3
from pelican import Pelican
from pelican.settings import read_settings

import git

log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.root.setLevel(logging.getLevelName(log_level))
_logger = logging.getLogger(__name__)

MAIN_DIR = "/tmp"
BLOG_DIR = "/tmp/blog"

client = boto3.client('lambda')
s3 = boto3.resource('s3')


def http_rebuild_blog(event, context):
    client.invoke(FunctionName="build-pelican-in-lambda-dev-async_rebuild_blog_from_git",
                  InvocationType='Event')


def async_handler(event, context):
    """Function entry"""
    _logger.info('Event: {}'.format(json.dumps(event)))

    build_blog_from_git(MAIN_DIR, BLOG_DIR)


def build_blog_from_git(main_dir, blog_dir):
    if os.path.isdir(blog_dir):
        shutil.rmtree(blog_dir)  # just fetch from the repo (including submodule dependencies)
    stdout, stderr = git.exec_command('clone', '--recurse-submodules',
                                      'https://github.com/alchrabas/blog.git', blog_dir, cwd=main_dir)
    os.chdir(blog_dir)
    settings = read_settings("pelicanconf.py")
    pelican = Pelican(settings)
    pelican.run()

    upload_recursively(blog_dir + "/output", "chrabasz.cz")

    _logger.info('Git stdout: {}, stderr: {}'.format(stdout.decode("utf-8"), stderr.decode("utf-8")))


def upload_recursively(path, bucketname):
    for root, dirs, files in os.walk(path):
        for file in files:
            s3.upload_file(os.path.join(root, file), bucketname, file)


if __name__ == "__main__":
    build_blog_from_git(".", "blog")

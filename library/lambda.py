#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: lambda
short_description: Manage AWS Lambda functions
description:
     - Allows for the management of Lambda functions.
version_added: '2.0'
requirements: [ boto3, base64, hashlib ]
options:
  name:
    description:
      - The name you want to assign to the function you are uploading. Cannot be changed.
    required: true
  state:
    description:
      - Create or delete Lambda function
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  runtime:
    description:
      - The runtime environment for the Lambda function you are uploading. Required when creating a function.
    default: null
    choices: [ 'nodejs', 'java8', 'python2.7' ]
  role_arn:
    description:
      - The Amazon Resource Name (ARN) of the IAM role that Lambda assumes when it executes your function to access any other Amazon Web Services (AWS) resources
    default: null
  handler:
    description:
      - The function within your code that Lambda calls to begin execution
    default: null
  path:
    description:
      - A .zip file containing your deployment package
    required: false
    default: null
    aliases: [ 'src' ]
  s3_bucket:
    description:
      - Amazon S3 bucket name where the .zip file containing your deployment package is stored
    required: false
    default: null
  s3_key:
    description:
      - The Amazon S3 object (the deployment package) key name you want to upload
    required: false
    default: null
  s3_object_version:
    description:
      - The Amazon S3 object (the deployment package) version you want to upload.
    required: false
    default: null
  description:
    description:
      - A short, user-defined function description. Lambda does not use this value. Assign a meaningful description as you see fit.
    required: false
    default: null
  timeout:
    description:
      - The function execution time at which Lambda should terminate the function.
    required: false
    default: 3
  memory_size:
    description:
      - The amount of memory, in MB, your Lambda function is given
    required: false
    default: 128
notes:
  - 'Currently this module only supports uploaded code via S3'
author:
    - 'Steyn Huizinga (@steynovich)'
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Create Lambda functions
tasks:
- name: looped creation
  lambda:
    name: '{{ item.name }}'
    state: present
    path: '{{ item.path }}'
    runtime: 'python2.7'
    role_arn: 'arn:aws:iam::987654321012:role/lambda_basic_execution'
    handler: 'hello_python.my_handler'
  with_items:
    - { name: HelloWorld, path: 'hello-code.zip' }
    - { name: ByeBye, path: 'bye-code.zip' }

# Basic Lambda function deletion
tasks:
- name: Delete Lambda functions HelloWorld and ByeBye
  lambda:
    name: '{{ item }}'
    state: absent
  with_items:
    - HelloWorld
    - ByeBye
'''

try:
    import boto
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import binascii
    HAS_BINASCII = True
except ImportError:
    HAS_BINASCII = False

try:
    import base64
    HAS_BASE64 = True
except ImportError:
    HAS_BASE64 = False

try:
    import hashlib
    HAS_HASHLIB = True
except ImportError:
    HAS_HASHLIB = False


def get_current_function(connection, function_name):
    try:
        return connection.get_function(FunctionName=function_name)
    except botocore.exceptions.ClientError as e:
        return False


def sha256sum(filename):
    hasher = hashlib.sha256()
    with open(filename, 'rb') as f:
        hasher.update(f.read())

    code_hash = hasher.digest()
    code_b64 = base64.b64encode(code_hash)
    hex_digest = code_b64.decode('utf-8')

    return hex_digest


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present','absent']),
        runtime=dict(type='str', choices=['nodejs','java8','python2.7'], default=None),
        role_arn=dict(type='str', default=None),
        handler=dict(type='str', default=None),
        path=dict(type='str', default=None, aliases=['src']),
        s3_bucket=dict(type='str', default=None),
        s3_key=dict(type='str', default=None),
        s3_object_version=dict(type='str', default=None),
        description=dict(type='str', default=''),
        timeout=dict(type='int', default=3),
        memory_size=dict(type='int', default=128),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[['path', 's3_key'],
                                               ['path', 's3_bucket'],
                                               ['path', 's3_object_version']])

    name = module.params.get('name')
    state = module.params.get('state').lower()
    runtime = module.params.get('runtime')
    role_arn = module.params.get('role_arn')
    handler = module.params.get('handler')
    s3_bucket = module.params.get('s3_bucket')
    s3_key = module.params.get('s3_key')
    s3_object_version = module.params.get('s3_object_version')
    path = module.params.get('path')
    description = module.params.get('description')
    timeout = module.params.get('timeout')
    memory_size = module.params.get('memory_size')

    check_mode = module.check_mode
    changed = False

    if not HAS_BOTO:
        module.fail_json(msg='Python module "boto" is missing, please install it')

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not HAS_BINASCII:
        module.fail_json(msg='Python module "binascii" is missing, please install it')

    if not HAS_HASHLIB:
        module.fail_json(msg='Python module "hashlib" is missing, please install it')

    if not HAS_BASE64:
        module.fail_json(msg='Python module "base64" is missing, please install it')


    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='lambda',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg=str(e))

    current_function = get_current_function(client, name)

    # Update existing Lambda function
    if state == 'present' and current_function:
        current_config = current_function['Configuration']
        current_code = current_function['Code']

        # Update function configuration
        func_kwargs = {'FunctionName': name}
        if current_config['Role'] != role_arn:
            func_kwargs.update({'Role': role_arn})
        if current_config['Handler'] != handler:
            func_kwargs.update({'Handler': handler})
        if current_config['Description'] != description:
            func_kwargs.update({'Description': description})
        if current_config['Timeout'] != timeout:
            func_kwargs.update({'Timeout': timeout})
        if current_config['MemorySize'] != memory_size:
            func_kwargs.update({'MemorySize': memory_size})

        # Unsupported mutation
        if not runtime:
            module.fail_json(msg='runtime parameter is required')
        if current_config['Runtime'] != runtime:
            module.fail_json(msg='Cannot change runtime. Please recreate the function')

        # Upload new configuration
        if len(func_kwargs) > 1:
            try:
                if not check_mode:
                    client.update_function_configuration(**func_kwargs)
                changed = True
            except (botocore.exceptions.ParamValidationError, botocore.exceptions.ClientError) as e:
                module.fail_json(msg=str(e))

        # Update code configuration
        code_kwargs = {'FunctionName': name}

        # Update S3 location
        if s3_bucket and s3_key:
            # If function is stored on S3 always update
            code_kwargs.update({'S3Bucket': s3_bucket,
                                'S3Key': s3_key})
            if s3_object_version:
                code_kwargs.update({'S3ObjectVersion': s3_object_version})

        # Compare local checksum, update remote code when different
        elif path:
            local_checksum = sha256sum(path)
            remote_checksum = current_config['CodeSha256']

            # Only upload new code when local code is different compared to the remote code
            if local_checksum != remote_checksum:
                try:
                    with open(path, 'rb') as f:
                        encoded_zip = f.read()
                    code_kwargs.update({'ZipFile' : encoded_zip})
                except IOError as e:
                    module.fail_json(msg=str(e))

        # Upload new code
        if len(code_kwargs) > 1:
            try:
                if not check_mode:
                    client.update_function_code(**code_kwargs)
                changed = True
            except (botocore.exceptions.ParamValidationError, botocore.exceptions.ClientError) as e:
                module.fail_json(msg=str(e))

        # We're done
        module.exit_json(changed=changed)

    # Function doesn't exists, create new Lambda function
    elif state == 'present':
        if not runtime:
            module.fail_json(msg='runtime parameter is required when creating a Lambda function')
        if not role_arn:
            module.fail_json(msg='role_arn parameter is required when creating a Lambda function')
        if not handler:
            module.fail_json(msg='handler parameter is required when creating a Lambda function')

        if s3_bucket and s3_key:
            # If function is stored on S3
            code = {'S3Bucket': s3_bucket, 'S3Key': s3_key}
            if s3_object_version:
                code.update({'S3ObjectVersion': s3_object_version})
        elif path:
            # If function is stored in local zipfile
            try:
                with open(path, 'rb') as f:
                    encoded_zip = f.read()

                code = {'ZipFile': encoded_zip}
            except IOError as e:
                module.fail_json(msg=str(e))

        else:
            module.fail_json(msg='Either S3 object or path to zipfile required')

        func_kwargs = {'FunctionName': name,
                       'Description': description,
                       'Runtime': runtime,
                       'Role': role_arn,
                       'Handler': handler,
                       'Code': code,
                       'Timeout': timeout,
                       'MemorySize': memory_size}

        # Finally try to create function
        try:
            if not check_mode:
                client.create_function(**func_kwargs)
            changed = True
        except (botocore.exceptions.ParamValidationError, botocore.exceptions.ClientError) as e:
            module.fail_json(msg=str(e))

        module.exit_json(changed=changed)

    # Delete existing Lambda function
    if state == 'absent' and current_function:
        try:
            if not check_mode:
                client.delete_function(FunctionName=name)
            changed = True
        except (botocore.exceptions.ParamValidationError, botocore.exceptions.ClientError) as e:
            module.fail_json(msg=str(e))

        module.exit_json(changed=changed)

    # Function already absent, do nothing
    elif state == 'absent':
        module.exit_json(changed=changed)


from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()

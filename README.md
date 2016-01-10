# Ansible playbook to regularly clean your Pocket account

I have the same problem as mrtazz: My reading is so long that I will never
manage to read it. So here is the OOTB Ansible playbook version of the
[https://github.com/mrtazz/pocketcleaner](pocketcleaner) because I like things to be entirely automated :)

It will setup a t2.nano AWS instance which regularly executes pocketcleaner.
## Prerequisites

 - A (overloaded) Pocket account
 - An AWS account (for a t2.nano instance) running the cron
 - Python/virtualenv

## Setup

Put a (maybe crypted, as you like) `vars.yml` into `vars` directory containing the [config vars](https://github.com/mrtazz/pocketcleaner#configuration) (will populate the `pocketcleaner.ini`), e.g.:

```
aws_region: eu-west-1
aws_ec2_keyname: <ec2keyname>
aws_ec2_image: ami-eda40d9e # UBUNTU AMI, e.g. from https://cloud-images.ubuntu.com/locator/ec2/
pocketcleaner_consumer_key: <consumer-key>
pocketcleaner_access_token: <access-token>
pocketcleaner_keep_count:   100
```

Run the playbook (AWS credentials have to be configured beforehand):

```
. setup.sh
ansible-playbook deploy-pocketcleaner.yml
```

## The future

 - Instead of EC2, use AWS Lambda Scheduling API once it becomes available via APIs

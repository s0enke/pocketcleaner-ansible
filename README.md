# Ansible playbook to regularly clean your Pocket account

I have the same problem as mrtazz: My reading is so long that I will never
manage to read it. So here is the OOTB Ansible playbook version of the
[pocketcleaner](https://github.com/mrtazz/pocketcleaner) because I like things to be entirely automated :)

It will setup a AWS Lambda function which can be invoked, e.g. by a timer or other Lambda events.

## Prerequisites

 - A (overloaded) Pocket account
 - An AWS account running the cron (Lambda)
 - Python/virtualenv to execute the Ansible playbook

## Setup

Put a (maybe crypted, as you like) `vars.yml` into `vars` directory containing the [config vars](https://github.com/mrtazz/pocketcleaner#configuration) (will populate the `pocketcleaner.ini`), e.g.:

```
aws_region: eu-west-1
aws_lambda_execution_role_arn: <a lambda execution role with no special permissions>
pocketcleaner_consumer_key: <consumer-key>
pocketcleaner_access_token: <access-token>
pocketcleaner_keep_count:   100
```

Run the playbook (AWS credentials have to be configured beforehand):

```
. setup.sh
ansible-playbook deploy-pocketcleaner.yml
```

Now setup e.g. a [scheduled Lambda event](http://docs.aws.amazon.com/lambda/latest/dg/with-scheduled-events.html) so your Pocket account gets cleaned regularly.

## The future

 - Script AWS Lambda Scheduling API once it becomes available via APIs

## License

MIT

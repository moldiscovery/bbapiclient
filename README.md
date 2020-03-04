# Minimal Oauth client to interact with BitBucket rest api

This script was almost copied from [ayush-sharma DevOps tools](https://github.com/ayush-sharma/infra_helpers)

## Requirements:

 - Python >= 3 
 - requests 
 - requests-oauthlib

## installation (I suggest to setup a virtualenv)

```
pip install -r requirements.txt 
```

## Setup and Usage

 - Go Bitbucket account settings -> OAuth -> Add Consumer
 
Set 

 - Repositories = Read
 - Account = Write
 - Callback URL = https://localhost 
 - This is a Private consumer = True

Once created take the account_id, key and secret and set the following variables in your environment:

```
 - BB_ACCOUNT_ID
 - BB_OAUTH_ID
 - BB_OAUTH_SECRET
```

Whenever command you'll have to:

 - Browse the given URL in your browser
 - copy the url generated by the BB 2FA from the navigation bar and feed the script with it

Some tips on usage:

List repos 

	$ BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py --operation listrepos --filereport 

Get group info: 

	$ BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py  --operation groupinfo --group fooDe

Set all repos permission ( IMPORTANT: if no group exist in the repos it will be created ): 

	$ BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py  --operation permissions --group foo --grant read

Set repo permission example: 

	$ BB_ACCOUNT_ID=id BB_OAUTH_ID=key BB_OAUTH_SECRET=secret python bbcli.py  --operation permissions --group foo --repo bar --grant read

# Migration Operations 

Collect backup infos for each group with

	$ BB_ACCOUNT_ID=moldiscovery BB_OAUTH_ID={key} BB_OAUTH_SECRET={secret} python bbcli.py --operation groupinfo --group groupname1  --filereport
	$ BB_ACCOUNT_ID=moldiscovery BB_OAUTH_ID={key} BB_OAUTH_SECRET={secret} python bbcli.py --operation groupinfo --group groupname2  --filereport
	$ .. 

Named report files will be created on the current dir


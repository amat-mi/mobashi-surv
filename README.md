# Mobashi-SURV

Server SURV of the Mobashi system.

# Installation

## Configuration for localdev

Only the first time, init Django models and create superuser, running the following commands while __inside__ the running devcontainer:

    cd /workspaces/mobashi-surv/mobashi-surv
    ../django_init.sh

## Configuration for prod

Only the first time, init Django models and create superuser, running the following commands while __outside__ the running devcontainer:

    sudo docker compose up -d
    sudo docker compose exec mobashi-surv /bin/bash
    ./django_init.sh

# Useful commands

Start all the services:

    sudo docker compose up -d

Opn a shell into running container for "mobashi-surv" service:

    sudo docker compose exec mobashi-surv /bin/bash

### Crypto

The package:

    https://github.com/incuna/django-pgcrypto-fields

allows you to encrypt fields in the PostgreSQL database transparently.

When you perform the first __migrate__, the package itself adds support for pgcrypto to the database,
executing the following SQL statement:

    create extension pgcrypto;
    
However, the package only works with the Public/Private key system and only if a passphrase has not been set to protect the secret key itself.

The two key files must be put inside the __secrets/django/[localdev|prod]/__ directory as __public.key__ and __private.key__ respectively, so that they end up mounted inside the container as:

     server/django_secrets/public.key
     server/django_secrets/private.key

For example they can be generated as described below.

Check the installed version of __gpg__ is 2.x:

    gpg --version
    
Generate the keys using one the following command: 

    gpg --full-generate-key

with the following settings:

    Please select what kind of key you want: [RESPOND 2]
    What keysize do you want? [RESPOND 2048]
    Key is valid for? [RESPOND 0]
    Real name: [RESPOND mobashisurv]
    Email address: [RESPOND mobashisurv@amat-mi.it]
    You need a Passphrase to protect your secret key. [DO NOT ENTER ANY PASSPHRASE!!!]
    
WARNING!!! If __gpg__ remains stuck on generating random bytes, it is necessary to open another terminal
and perform operations that engage the disk, or download files from the Internet, otherwise it may take
several minutes before enough random values are available to generate the keys!!!

Export the public key, specifying the email address used earlier:

    gpg -a --export mobashisurv@amat-mi.it > secrets/django/[localdev|prod]/public.key

Get the identifier of the private key:
    
    gpg --list-secret-keys
    
    /home/prizzi/.gnupg/pubring.kbx
    -------------------------------
    sec   dsa2048 2020-03-09 [SC]
          XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    uid           [ultimate] mobashisurv <mobashisurv@amat-mi.it>
    ssb   elg2048 2020-03-09 [E]
    
The value on the second line of __sec__ (Ex: XXXXX) is the identifier of the __private__ key.

Export the private key, specifying its identifier:

    gpg -a --export-secret-keys <ID_PRIVATE> > secrets/django/[localdev|prod]/private.key

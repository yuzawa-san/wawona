# wawona

by @yuzawa-san

Easily make office reservations in sequoia from the command line.
This tool is specifically for viewing the next two week's bookings from coworkers that you have followed, and then for booking multiple days at a time.

## Setup

- python 3 must be installed
- (optional) use a virtualenv:
- install dependencies: `pip install -r requirements.txt`

## Usage 

- (optional) enter your virtualenv
- run it: `python wawona.py`
- provide email and password (and MFA token), you will be prompted to re-authorise periodically
- view reservations
- optionally book days (or not, just hit return to exit)

## Notes

- not affliated with sequoia
- uses public endpoints discovered from the web UI
- no warranty or stability guarantees, could break one day if something changes on their end
- password/token is stored in system keychain
- no intention to add ability book seats since that flow is too complex
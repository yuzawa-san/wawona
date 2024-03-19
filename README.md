# wawona

by @yuzawa-san

Easily make office reservations in sequoia from the command line.
This tool is specifically for viewing the next two week's bookings from coworkers that you have followed, and then for booking multiple days at a time.

## Install

- python 3 must be installed
- (recommended) use a virtualenv:
- install dependencies: `python setup.py install`

## Usage 

- (optional) enter your virtualenv
- run it: `./wawona`
- provide email and password (and MFA token), you will be prompted to re-authorise periodically
- view reservations
- optionally book days (or not, just hit return to exit)

```
+----------------------+-----+-----+-----+-----+-----+
| Week of 11 Mar       | Mon | Tue | Wed | Thu | Fri |
|                      | 11  | 12  | 13  | 14  | 15  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | x   | x   | x   | x   | x   |
+----------------------+-----+-----+-----+-----+-----+
| Paul Wawona          |     |     | x   |     | x   |
+----------------------+-----+-----+-----+-----+-----+
| Juan Fnulwoln        |     | x   |     | x   |     |
+----------------------+-----+-----+-----+-----+-----+
| Maeve Melwosniwnaiko |     | x   | x   | x   |     |
+----------------------+-----+-----+-----+-----+-----+
| Week of 18 Mar       | Mon | Tue | Wed | Thu | Fri |
|                      | 18  | 19  | 20  | 21  | 22  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | x   | x   | x   |     |     |
+----------------------+-----+-----+-----+-----+-----+
[?] What dates do you want to reserve?: 
 > [X] Thu 14 Mar
   [X] Fri 15 Mar
   [X] Mon 18 Mar
   [X] Tue 19 Mar
   [X] Wed 20 Mar
   [ ] Thu 21 Mar
   [ ] Fri 22 Mar

````

## Notes

- not affliated with sequoia
- uses public endpoints discovered from the web UI
- no warranty or stability guarantees, could break one day if something changes on their end
- password/token is stored in system keychain
- no intention to add ability book seats since that flow is too complex
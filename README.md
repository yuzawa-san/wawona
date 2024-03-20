# wawona

by [@yuzawa-san](https://github.com/yuzawa-san/)

![PyPI - Version](https://img.shields.io/pypi/v/wawona)

Easily make office reservations in sequoia from the command line.
This tool is specifically for viewing the next two week's bookings from coworkers that you have followed, and then for booking multiple days at a time.

## Install

The easiest way is probably using [Homebrew](https://brew.sh/).
A self-maintained tap is available for use. To install tap:
```console
brew tap yuzawa-san/tap
```

To install:
```console
brew update
brew install wawona
```

To update:
```console
brew update
# upgrade all Homebrew software
brew upgrade
# update just this
brew upgrade wawona
```

## Usage 

- run it from your terminal: `wawona`
- provide email and password (and MFA token), you will be prompted to re-authorise periodically
- view reservations
- optionally book days (or not, just hit return to exit)

```
+----------------------+-----+-----+-----+-----+-----+
| WEEK OF 11 Mar       | Mon | Tue | Wed | Thu | Fri |
|                      | 11  | 12  | 13  | 14  | 15  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | ✅   | ✅   | ✅   | ✅   | ✅   |
+----------------------+-----+-----+-----+-----+-----+
| Paul Wawona          |     |     | ✅   |     | ✅   |
+----------------------+-----+-----+-----+-----+-----+
| Juan Fnulwoln        |     | ✅   |     | ✅   |     |
+----------------------+-----+-----+-----+-----+-----+
| Maeve Melwosniwnaiko |     | ✅   | ✅   | ✅   |     |
+----------------------+-----+-----+-----+-----+-----+
| WEEK OF 18 Mar       | Mon | Tue | Wed | Thu | Fri |
|                      | 18  | 19  | 20  | 21  | 22  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | ✅   | ✅   | ✅   |     |     |
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
- named for the [tree](https://en.wikipedia.org/wiki/Wawona_Tree)
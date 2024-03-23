# 🌲 wawona 🌲

by [@yuzawa-san](https://github.com/yuzawa-san/)

[![PyPI - Version](https://img.shields.io/pypi/v/wawona)](https://pypi.org/project/wawona/)

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
| WEEK OF 11 MAR       | Mon | Tue | Wed | Thu | Fri |
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
| WEEK OF 18 MAR       | Mon | Tue | Wed | Thu | Fri |
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
- named for the [drive-thru sequoia](https://en.wikipedia.org/wiki/Wawona_Tree)

## Reset

If you need to reset to factory defaults (maybe if you changed your password), remove the configuration:

```
rm -rf ~/.config/wawona/
```
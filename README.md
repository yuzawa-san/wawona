# 🌲 wawona 🌲

by [@yuzawa-san](https://github.com/yuzawa-san/)

[![PyPI - Version](https://img.shields.io/pypi/v/wawona)](https://pypi.org/project/wawona/)

Easily make office reservations in sequoia from the command line.
This tool is provides streamlined workflows:

- viewing the next two week's bookings from coworkers that you have followed
- booking multiple days at a time
- doing space reservations (with the ability to save your preferred space)
- if an option contains a single choice, automatically select that choice

```
+----------------------+-----+-----+-----+-----+-----+
| WEEK OF 11 MAR       | Mon | Tue | Wed | Thu | Fri |
|                      | 11  | 12  | 13  | 14* | 15  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | x   | x   | x   |     | x   |
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
| Me                   | x   | x   |     |     |     |
+----------------------+-----+-----+-----+-----+-----+
[?] Date(s) to reserve (press return for none): 
 > [X] Thu 14 Mar
   [X] Wed 20 Mar
   [ ] Thu 21 Mar
   [ ] Fri 22 Mar

+----------------------+-----+-----+-----+-----+-----+
| WEEK OF 11 MAR       | Mon | Tue | Wed | Thu | Fri |
|                      | 11  | 12  | 13  | 14* | 15  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | x   | x   | x   | x   | x   |
+----------------------+-----+-----+-----+-----+-----+
| WEEK OF 18 MAR       | Mon | Tue | Wed | Thu | Fri |
|                      | 18  | 19  | 20  | 21  | 22  |
+----------------------+-----+-----+-----+-----+-----+
| Me                   | x   | x   | x   |     |     |
+----------------------+-----+-----+-----+-----+-----+

```

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

- Run it from your terminal: `wawona`
- On initial run, you will be asked provide configuration: email and password.
- You may be prompted to for an MFA token periodically.

### Reset

If you need to reset to factory defaults (maybe if you changed your password), remove the configuration:

```console
rm -rf ~/.config/wawona/
```

## Notes

- Not affliated with sequoia
- Uses public endpoints discovered from the web UI
- No warranty or stability guarantees, could break one day if something changes on their end
- Password/token is stored in system keychain
- Add/remove followers using the app. basically if it is not here or it breaks here, use the real app/site.
- Named for the [drive-thru sequoia](https://en.wikipedia.org/wiki/Wawona_Tree)

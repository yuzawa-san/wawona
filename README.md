# 🌲 wawona 🌲

by [@yuzawa-san](https://github.com/yuzawa-san/)

[![PyPI - Version](https://img.shields.io/pypi/v/wawona)](https://pypi.org/project/wawona/)

Easily make office reservations in sequoia from the command line.
This tool is provides streamlined workflows:

- viewing the next two week's bookings from coworkers that you have followed (in the app/[site](https://px.sequoia.com/workplace))
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
Waiting for pending tasks...
Reservation Acknowledgement Pending:

  Mar 27 New York Reservation
  Complete Self-Screening
  Seat Not Selected

[?] Complete task? (Y/n): 
[?] I am healthy and not sick?: Yes (only choice)
[?] Floor: Floor 2 (only choice)

 X X
 X X   X X
 X O   O X   O O O X O
 X X   O O   O * $ O $
 O O   O O
 O O   O O   O O O O O
 O O   O O   O X O O O

* preferred    O free    $ booked by someone you are following    X booked
[?] Space: 
   Desk 5
   Desk 6
   Desk 7
   Desk 8 (Guillaume Rucpelzsva)
   Desk 9
   Desk 10
 > Desk 11
   Desk 12 (Juan Fnulwoln)
   Desk 13
   Desk 14 (Maeve Melwosniwnaiko)
   Desk 15
   Desk 16
   Desk 17

You have booked 'Desk 11'
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
- Use the up/down arrows, spacebar, and return keys to select items in lists
- Troubleshooting errors with `wawona --verbose`

### Reset

If you need to reset to factory defaults (maybe if you changed your password), remove the configuration:

```console
wawona reset
```

As a last resort, if all else fails:

```console
rm -rf ~/.config/wawona/
```

## Notes

- Not affliated with sequoia
- Does not support SSO
- Uses public endpoints discovered from the web UI
- No warranty or stability guarantees, could break one day if something changes on their end
- Password/token is stored in system keychain
- Add/remove followers using the app.
- Basically if it is not here or it breaks here, use the real app/site.
- Named for the [drive-thru sequoia](https://en.wikipedia.org/wiki/Wawona_Tree)

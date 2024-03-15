import json
import os
import sys
import requests
from datetime import date, timedelta
from os.path import isfile, isdir
from getpass import getpass
from texttable import Texttable
import inquirer
import keyring

config_path = "%s/.config/sequoia-workplace-bookings" % os.environ["HOME"]
config_file = "%s/config.json" % config_path


BROWSER_HASH="1032275734"
HEADERS = {
    'authority': 'hrx-backend.sequoia.com',
    'accept': 'application/json',
    'agent': 'admin',
    'content-type': 'application/json;charset=UTF-8',
    'devicetype': '4',
    'locale-timezone': 'America/New_York',
    'origin': 'https://login.sequoia.com',
    'referer': 'https://login.sequoia.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}
KEYRING_EMAIL="login.sequoia.com"
KEYRING_TOKEN="hrx-backend.sequoia.com"

def get_config():
    if not isfile(config_file):
        return {}
    with open(config_file) as f:
        return json.load(f)

def put_config(config):
    if not isdir(config_path):
        os.makedirs(config_path, exist_ok=True)
    with open(config_file,'w') as f:
        json.dump(config, f)

def check(response):
    if response.status_code != 200:
        print(response, response.json())
        raise Exception("request failed")
    return response

def get_token(refresh=False):
    config = get_config()
    email = config.get("email")
    if not email:
        email = input("Email: ")
        config["email"] = email
    token = keyring.get_password(KEYRING_TOKEN, email)
    if token and not refresh:
        return token
    response = check(requests.post("https://hrx-backend.sequoia.com/idm/v1/contacts/verify-email", headers=HEADERS, json={"email":email}))
    password = keyring.get_password(KEYRING_EMAIL, email)
    if not password:
        password = getpass("Password for %s: " % email)
    response = check(requests.post("https://hrx-backend.sequoia.com/idm/users/login", headers=HEADERS, json={"email":email,"password":password,"browserHash":BROWSER_HASH,"userType":"employee"}))
    login_json = response.json()
    user_details = login_json["data"]["userDetails"]
    token = user_details["apiToken"]
    if user_details["oktaStatus"] == "MFA_CHALLENGE":
        mfa_code = input("MFA Code: ")
        headers = {"apitoken": token}
        headers.update(HEADERS)
        response = check(requests.post("https://hrx-backend.sequoia.com/idm/users/login/verify-mfa", headers=headers, json={"passCode":mfa_code,"browserHash":BROWSER_HASH}))
    keyring.set_password(KEYRING_EMAIL, email, password)
    keyring.set_password(KEYRING_TOKEN, email, token)
    put_config(config)
    return token

def token_headers(token):
    headers = {"token": token}
    headers.update(HEADERS)
    return headers

def get_locations(token):
    response = check(requests.get("https://hrx-backend.sequoia.com/rtw/resv/client/locations", headers=token_headers(token)))
    return [(x["locationName"], x["locationId"]) for x in response.json()["data"]["locations"]]

def format_date(dt):
    return "%02d-%02d-%d" % (dt.day, dt.month, dt.year)

def parse_date(dt):
    day, month, year = dt.split("-")
    return date(int(year), int(month), int(day))

def get_summary(token, start, end):
    response = check(requests.get("https://hrx-backend.sequoia.com/rtw/client/dashboard/summary?statStart=%s&statEnd=%s" % (format_date(start), format_date(end)), headers=token_headers(token)))
    out = set()
    for stat in response.json()["data"]["weeklyStats"]:
        out.add(parse_date(stat["date"]))
    return out
    
def get_followings(token, start, end):
    response = check(requests.get("https://hrx-backend.sequoia.com/rtw/client/followings?startDate=%s&endDate=%s" % (format_date(start), format_date(end)), headers=token_headers(token)))
    out = []
    for user in response.json()["data"]["followings"]:
        name = user["fullName"]
        reservations = user.get("reservationsMetadata",[])
        days = set()
        if reservations:
            for reservation in reservations:
                year, month, day = reservation["reservationStartTime"].split(" ")[0].split("-")
                dt = date(int(year), int(month), int(day))
                days.add(dt)
            out.append((name, days))
        
    return out

def add_reservations(token, location_id, dates):
    body = {
        "reservationType": "LOCATION",
        "locationId": location_id,
        "reservations": []
    }
    for date in dates:
        iso_date = date.isoformat()
        body['reservations'].append({
            "startTimeUtc": "%sT13:00:00Z" % iso_date,
            "endTimeUtc": "%sT20:59:00Z" % iso_date,
            "isPrivate": False
        })
    response = check(requests.post("https://hrx-backend.sequoia.com/rtw/resv/client/reservations", headers=token_headers(token), json=body))
    print(response.json())

token = get_token()
today = date.today()
weekday = today.weekday()
if weekday < 5:
    start = today - timedelta(days=weekday)
else:
    start = today + timedelta(days=7-weekday)
days = 14
end = start + timedelta(days=days)
try:
    booked = get_summary(token, start, end)
except:
    token = get_token(True)
    booked = get_summary(token, start, end)
followings = get_followings(token, start, end)
choices = []
defaults = []
weeks = [[],[]]
for day_offset in range(days):
    day = start + timedelta(days=day_offset)
    weekday = day.weekday()
    if weekday < 5:
        weeks[day_offset // 7].append(day)
rows = []
for week in weeks:
    header = ["Week of %s" % week[0].strftime('%d %b')]
    booking_row = ["Me"]
    rows.append(header)
    rows.append(booking_row)
    for day in week:
        header.append(day.strftime('%a\n%d'))
        is_booked = day in booked
        booking_row.append("x" if is_booked else "")
        if day >= today:
            choices.append((day.strftime('%a %d %b'), day))
            if is_booked:
                defaults.append(day)
    for name, days in followings:
        user_row = [name]
        add_row = False
        for day in week:
            if day in days:
                entry = "x"
                add_row = True
            else:
                entry = ""
            user_row.append(entry)
        if add_row:
            rows.append(user_row)

t = Texttable(max_width=0)
t.add_rows(rows, header=False)
print(t.draw())

locations = get_locations(token)
if len(locations) == 0:
    raise Exception("No locations")
if len(locations) == 1:
    location_id = locations[0][1]
else:
    questions = [
        inquirer.List(
            "location",
            message="What office do you want to reserve?",
            choices=locations,
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        raise Exception("No location")
    location_id = answers['location']

questions = [
    inquirer.Checkbox(
        "dates",
        message="What dates do you want to reserve?",
        choices=choices,
        default=defaults,
    ),
]

answers = inquirer.prompt(questions)
if not answers:
    raise Exception("No dates")
to_book = []
for date in answers["dates"]:
    if date not in defaults:
        to_book.append(date)
if to_book:
    add_reservations(token, location["locationId"], to_book)
else:
    print("No reservations added.")
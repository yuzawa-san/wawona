import json
import os
import sys
import re
import time
import requests
from datetime import date, datetime, time, timedelta
from os.path import isfile, isdir
from getpass import getpass
from texttable import Texttable
import inquirer
import keyring
import pytz

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
CHECK_MARK = "\u2705"

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
        email = inquirer.text(message="Email")
        config["email"] = email
    token = keyring.get_password(KEYRING_TOKEN, email)
    if token and not refresh:
        return token
    response = check(requests.post("https://hrx-backend.sequoia.com/idm/v1/contacts/verify-email", headers=HEADERS, json={"email":email}))
    password = keyring.get_password(KEYRING_EMAIL, email)
    if not password:
        password = inquirer.password(message='Password')
    response = check(requests.post("https://hrx-backend.sequoia.com/idm/users/login", headers=HEADERS, json={"email":email,"password":password,"browserHash":BROWSER_HASH,"userType":"employee"}))
    login_json = response.json()
    login_data = login_json["data"]
    user_details = login_data["userDetails"]
    token = user_details["apiToken"]
    if user_details["oktaStatus"] == "MFA_CHALLENGE":
        factors = login_data.get("factors")
        if factors:
            factor = factors[0]
            print("Using MFA %s %s" % (factor.get("factorType","unknown"), factor.get("profile",{}).get("phoneNumber")))
        mfa_code = inquirer.text(message="MFA Code")
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
    return [(x["locationName"], x) for x in response.json()["data"]["locations"]]

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

def pretty_time(tz, day, time):
    return tz.localize(datetime.combine(day, time)).astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')

def add_reservations(token, location, dates):
    body = {
        "reservationType": "LOCATION",
        "locationId": location["locationId"],
        "reservations": []
    }
    tz = pytz.timezone(location["locationTimezone"])
    for day in dates:
        iso_date = day.isoformat()
        body['reservations'].append({
            "startTimeUtc": pretty_time(tz, day, time(9)),
            "endTimeUtc": pretty_time(tz, day, time(16,59)),
            "isPrivate": False
        })
    check(requests.post("https://hrx-backend.sequoia.com/rtw/resv/client/reservations", headers=token_headers(token), json=body))

def do_inquiry(message, choices, default=None):
    if len(choices) == 0:
        raise Exception("No choices")
    if len(choices) == 1:
        choice = choices[0]
        print("[\033[33m?\033[0m] %s: \033[32m%s\033[0m (only choice)" % (message, choice[0]))
        return choice[1]
    questions = [
        inquirer.List(
            "choice",
            message=message,
            choices=choices,
            default=default
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        raise Exception("No choice")
    return answers['choice']

def get_pending_tasks(token):
    response = check(requests.get("https://hrx-backend.sequoia.com/rtw/client/pending-task", headers=token_headers(token)))
    return response.json()["data"]["tasks"]

def get_task(token, task_id):
    response = check(requests.get("https://hrx-backend.sequoia.com/rtw/client/task/info?taskId=%s" % task_id, headers=token_headers(token)))
    return response.json()["data"]

def respond_to_task(token, task_id, answers):
    check(requests.post("https://hrx-backend.sequoia.com/rtw/client/task-response", headers=token_headers(token), json={"taskId":task_id,"response":answers}))

def get_floors(token, task_id):
    response = check(requests.get("https://hrx-backend.sequoia.com/rtw/client/space-bookings/floors?taskId=%s" % task_id, headers=token_headers(token)))
    return [(x["floorName"], x["floorId"]) for x in response.json()["data"]["floors"] if x["status"] == "active"]

def get_spaces(token, adjective, task_id, floor_id, start_time, end_time):
    url = "https://hrx-backend.sequoia.com/rtw/client/space-bookings/%s/spaces?taskId=%s&floorId=%s&startTime=%s&endTime=%s" % (adjective, task_id, floor_id, start_time, end_time)
    response = check(requests.get(url, headers=token_headers(token)))
    return response.json()["data"]["spaces"]

def reserve_space(token, task_id, start_time, end_time, space_id, user_id, reservation_id):
    response = check(requests.post("https://hrx-backend.sequoia.com/rtw/client/space-bookings/space", headers=token_headers(token), json={"taskId":task_id,"startTime":start_time,"endTime":end_time,"spaceId":space_id,"userId":user_id,"reservationId":reservation_id}
))
    return response.json()["data"]["label"]

def get_space(token, task, floor_id):
    task_id = task["taskId"]
    start_time = task["reservationStartTime"]
    end_time = task["reservationEndTime"]
    available_spaces = get_spaces(token, "available", task_id, floor_id, start_time, end_time)
    preferred_space_id = inquirer.text(message="Preferred space ID (press return for none)")
    all_spaces = []
    available_space_set = set()
    for available_space in available_spaces:
        space_id = available_space["spaceId"]
        unique_space_id = available_space["uniqueSpaceId"]
        if space_id == preferred_space_id:
            return unique_space_id
        all_spaces.append(available_space)
        available_space_set.add(unique_space_id)
    booked_spaces = get_spaces(token, "booked", task_id, floor_id, start_time, end_time)
    default = None
    for booked_space in booked_spaces:
        space_id = booked_space["spaceId"]
        if space_id == preferred_space_id:
            default = booked_space["uniqueSpaceId"]
        all_spaces.append(booked_space)
    all_spaces.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s["label"])])
    choices = []
    for space in all_spaces:
        raw_label = space["label"]
        first_name = space.get("firstName")
        if first_name:
            label = "\033[31m%s (%s %s)\033[0m" % (raw_label, first_name, space["lastName"])
        else:
            label = "\033[32m%s\033[0m" % raw_label
        choices.append((label, space["uniqueSpaceId"]))
    while True:
        print("Preferred space is not available")
        unique_space_id = do_inquiry("Space", choices, default)
        if unique_space_id in available_space_set:
            return unique_space_id

def run_tasks(token):
    pending_tasks = get_pending_tasks(token)
    for task in pending_tasks:
        task_id = task["taskId"]
        print(task)
        task_metadata = task["taskMetadata"]
        task_data = task_metadata.get("data")
        if not task_data:
            continue
        card_info = task_metadata["cardInfo"]
        print("You have a pending task - %s:\n\n\t%s %s %s\n\t%s\n\t%s\n" % (
            task["taskTitle"],
            card_info.get("displayTitle",""),
            card_info.get("title",""),
            card_info.get("heading",""),
            card_info.get("basicSubtitle", ""),
            card_info.get("caption", "")
        ))
        if not inquirer.confirm("Complete task?", default=True):
            continue
        questions = task_data["questions"]
        if not questions or not task_data["hasQuestionnaire"]:
            raise Exception("Task without questionaire not supported")
        if task_data["hasDocumentAck"]:
            raise Exception("Task with document acknowledgement not supported")
        answers = []
        for question in questions:
            question_id = question["questionId"]
            question_type = question["answerType"]
            if question_type != "SINGLE_SELECT":
                raise Exception("Question type %s not supported" % question_type)
            question_category = question["questionCategory"]
            if question_category != "ALL_USERS":
                raise Exception("Question category %s not supported" % question_category)
            raw_choices = question["choices"]
            if not raw_choices:
                raise Exception("Question missing choices")
            choices = []
            for raw_choice in raw_choices:
                choice_type = raw_choice["choiceType"]
                if choice_type != "QUALIFY":
                    raise Exception("Choice type %s not supported" % choice_type)
                choices.append([raw_choice["choiceLabel"], raw_choice["choiceId"]])
            choice_id = do_inquiry(question["questionTitle"].strip(), choices)
            answers.append({"questionId": question_id, "choice_id": choice_id})
        respond_to_task(token, task_id, answers)
        if not task["spaceBookingEnabled"]:
            continue
        floors = get_floors(token, task_id)
        floor_id = do_inquiry("Floor", floors)
        space_id = get_space(token, task, floor_id)
        start_time = task["reservationStartTime"]
        end_time = task["reservationEndTime"]
        user_id = task["recipientId"]
        reservation_id = task["reservationId"]
        space_label = reserve_space(token, task_id, start_time, end_time, space_id, user_id, reservation_id)
        print("You have booked '%s'" % space_label)

def print_weeks(weeks, today, booked, followings, choices):
    rows = []
    for week in weeks:
        label = "WEEK OF %s" % week[0].strftime('%d %b').upper()
        header = [label]
        booking_row = ["Me"]
        rows.append(header)
        rows.append(booking_row)
        for day in week:
            day_label = day.strftime('%a\n%d')
            if day == today:
                day_label = "%s*" % day_label
            header.append(day_label)
            is_booked = day in booked
            booking_row.append(CHECK_MARK if is_booked else "")
            if not is_booked and day >= today:
                choices.append((day.strftime('%a %d %b'), day))
        for name, days in followings:
            user_row = [name]
            add_row = False
            for day in week:
                if day in days:
                    entry = CHECK_MARK
                    add_row = True
                else:
                    entry = ""
                user_row.append(entry)
            if add_row:
                rows.append(user_row)
    t = Texttable(max_width=0)
    t.add_rows(rows, header=False)
    print(t.draw())

def run():
    print("\U0001F332 \033[32mW A W O N A\033[0m \U0001F332\n\nhttps://github.com/yuzawa-san/wawona\n")
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
    run_tasks(token)
    followings = get_followings(token, start, end)
    choices = []
    weeks = [[],[]]
    for day_offset in range(days):
        day = start + timedelta(days=day_offset)
        weekday = day.weekday()
        if weekday < 5:
            weeks[day_offset // 7].append(day)
    print_weeks(weeks, today, booked, followings, choices)
    if not choices:
        return

    locations = get_locations(token)
    location = do_inquiry("Office", locations)

    questions = [
        inquirer.Checkbox(
            "dates",
            message="Date to reserve (press return for none)",
            choices=choices,
        ),
    ]

    answers = inquirer.prompt(questions)
    if not answers:
        return
    to_book = answers["dates"]
    if not to_book:
        print("No reservations added.")
        return
    add_reservations(token, location, to_book)
    booked = get_summary(token, start, end)
    print_weeks(weeks, today, booked, [], [])
    if today in to_book:
        print("Waiting for pending tasks...")
        time.sleep(10)
        run_tasks()
if __name__ == "__main__":
    run()
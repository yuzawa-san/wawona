import json
import locale
import os
import re
import sys
from datetime import date, datetime, time, timedelta
from os.path import isfile, isdir
from time import sleep
from urllib.parse import unquote

import inquirer
import keyring
import pytz
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from texttable import Texttable

config_path = "%s/.config/wawona" % os.environ["HOME"]
config_file = "%s/config.json" % config_path

TERMINAL_CHAR_ASPECT_RATIO = 8 / 10
FLOOR_PLAN_BUFFER = 4
FLOOR_PLAN_COLS = 120
COLOR_AVAILABLE = "32"
COLOR_BOOKED_FOLLOWING = "36"
COLOR_BOOKED = "31"
COLOR_PREFERRED = "35"
DOT = "\u25CF"

BROWSER_HASH = "1032275734"
HEADERS = {
    'authority': 'hrx-backend.sequoia.com',
    'accept': 'application/json',
    'agent': 'admin',
    'content-type': 'application/json;charset=UTF-8',
    'devicetype': '4',
    'locale-timezone': 'America/New_York',
    'origin': 'https://login.sequoia.com',
    'referer': 'https://login.sequoia.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/122.0.0.0 Safari/537.36'
}
KEYRING_TOKEN = "hrx-backend.sequoia.com"
CHECK_MARK = "\u2705"
CONFIG_VERSION = 1
YOU = "You"

VERBOSE = False
for arg in sys.argv:
    if arg == "reset":
        print("Removing config file")
        os.remove(config_file)
    elif arg == "--verbose":
        VERBOSE = True


class ApiException(Exception):
    pass


def api_call(method, url, **kwargs):
    if VERBOSE:
        print("API REQUEST: %s %s %s %s" % (method, url, kwargs.get("headers"), kwargs.get("json")))
    response = requests.request(method, url, **kwargs)
    status_code = response.status_code
    response_headers = response.headers
    content_type = response_headers.get('Content-Type') or ''
    response_json = {}
    if content_type.startswith('application/json'):
        response_json = response.json()
    if VERBOSE:
        print("API RESPONSE: %s %s %s" % (status_code, response_headers, response_json))
    if status_code != 200:
        if status_code == 400 and not response_json.get("success"):
            raise ApiException(response_json.get("message"))
        raise ApiException("%s %s %s %s %s %s" %
                           (method, url, kwargs.get("headers"), status_code, response_headers, response_json))
    return response_json


def get_token(refresh=False):
    token = keyring.get_password(KEYRING_TOKEN, KEYRING_TOKEN)
    if token and not refresh:
        return token
    print("Loading auth flow in standalone Chrome...")
    print("NOTE: If you get the alert with 'chromedriver cannot be opened because the developer cannot be verified.',"
          "select 'Cancel' to proceed.")
    print("PROTIP: Enable 'Remember Me' and 'Keep me signed in' and 'Trusted Device' to speed up subsequent logins.")
    chrome_options = Options()
    chrome_options.add_argument("user-data-dir=%s/selenium" % config_path)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://login.sequoia.com/?redirect=https://px.sequoia.com/workplace/")
    try:
        WebDriverWait(driver, 300).until(EC.url_to_be("https://px.sequoia.com/workplace/"))
        cookies = driver.get_cookies()
        if VERBOSE:
            print("COOKIES", cookies)
        for cookie in cookies:
            if cookie["name"] == "_sc":
                token = json.loads(unquote(cookie["value"]))["sessionToken"]
                keyring.set_password(KEYRING_TOKEN, KEYRING_TOKEN, token)
                return token
        raise ApiException("Failed to fetch token")
    finally:
        driver.quit()


def get_config():
    config: dict[str, str] = {}
    if isfile(config_file):
        with open(config_file) as f:
            config = json.load(f)
    if CONFIG_VERSION == int(config.get("version", "0")):
        return config
    config["version"] = str(CONFIG_VERSION)
    hours = []
    for hour in range(24):
        formatted = datetime.combine(date.today(), time(hour)).strftime(locale.nl_langinfo(locale.T_FMT_AMPM))
        hours.append((formatted, hour))
    questions = [
        # NOTE: this does not have location
        inquirer.Text(
            "preferred_space_id",
            message="Preferred space ID (press return for none)",
        ),
        inquirer.List(
            "start_hour",
            message="Start of Day (for reservations)",
            choices=hours,
            default=8
        ),
        inquirer.List(
            "end_hour",
            message="End of Day (for reservations)",
            choices=hours,
            default=18
        ),
    ]
    answers = inquirer.prompt(questions)
    config.update(answers)
    token = keyring.get_password(KEYRING_TOKEN, KEYRING_TOKEN)
    if token:
        keyring.delete_password(KEYRING_TOKEN, KEYRING_TOKEN)
    # test configuration
    get_token()
    # only persist configuration if test worked
    if not isdir(config_path):
        os.makedirs(config_path, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f)
    return config


def token_headers(token):
    headers = {"token": token}
    headers.update(HEADERS)
    return headers


def get_locations(token):
    response = api_call(
        method='GET', url="https://hrx-backend.sequoia.com/rtw/resv/client/locations", headers=token_headers(token))
    return [(x["locationName"], x) for x in response["data"]["locations"]]


def format_date(dt):
    return "%02d-%02d-%d" % (dt.day, dt.month, dt.year)


def parse_date(dt):
    day, month, year = dt.split("-")
    return date(int(year), int(month), int(day))


def get_summary(token, start, end):
    response = api_call(method='GET',
                        url="https://hrx-backend.sequoia.com/rtw/client/dashboard/summary?statStart=%s&statEnd=%s" % (
                            format_date(start), format_date(end)), headers=token_headers(token))
    out = set()
    for stat in response["data"]["weeklyStats"]:
        out.add(parse_date(stat["date"]))
    return out


def get_followings(token, start, end):
    response = api_call(method='GET',
                        url="https://hrx-backend.sequoia.com/rtw/client/followings?startDate=%s&endDate=%s" % (
                            format_date(start), format_date(end)), headers=token_headers(token))
    out = {}
    followings = response["data"]["followings"]
    if not followings:
        print("You are not following any coworkers.\n"
              "Add them in https://px.sequoia.com/workplace or the app, and they will appear calendar below.")
    for user in followings:
        name = user["fullName"]
        reservations = user.get("reservationsMetadata", [])
        days = set()
        out[name] = days
        if reservations:
            for reservation in reservations:
                year, month, day = reservation["reservationStartTime"].split(" ")[0].split("-")
                dt = date(int(year), int(month), int(day))
                days.add(dt)
    return out


def pretty_time(dt):
    return dt.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')


def add_reservations(token, location, dates, config):
    body = {
        "reservationType": "LOCATION",
        "locationId": location["locationId"],
        "reservations": []
    }
    tz = pytz.timezone(location["locationTimezone"])
    # the earliest start will be the top of the next hour
    min_start = (datetime.now(tz) + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    check_tasks = False
    for day in dates:
        start = tz.localize(datetime.combine(day, time(int(config["start_hour"]))))
        if start <= min_start:
            start = min_start
            # make sure we wait for pending tasks since we are close enough to the start of the reservation
            check_tasks = True
        # the end needs to be a minute before the end start of the last hour
        end = tz.localize(datetime.combine(day, time(int(config["end_hour"]))) - timedelta(minutes=1))
        if start < end:
            body['reservations'].append({
                "startTimeUtc": pretty_time(start),
                "endTimeUtc": pretty_time(end),
                "isPrivate": False
            })
    if body['reservations']:
        api_call(
            method='POST', url="https://hrx-backend.sequoia.com/rtw/resv/client/reservations",
            headers=token_headers(token),
            json=body)
    return check_tasks


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
    response = api_call(method='GET', url="https://hrx-backend.sequoia.com/rtw/client/pending-task",
                        headers=token_headers(token))
    return [x["taskId"] for x in response["data"]["tasks"]]


def get_task(token, task_id):
    response = api_call(method='GET',
                        url="https://hrx-backend.sequoia.com/rtw/client/task/info?taskId=%s" % task_id,
                        headers=token_headers(token))
    return response["data"]


def respond_to_task(token, task_id, answers):
    api_call(method='POST', url="https://hrx-backend.sequoia.com/rtw/client/task-response",
             headers=token_headers(token),
             json={"taskId": task_id, "response": answers})


def get_floors(token, task_id):
    response = api_call(
        method='GET', url="https://hrx-backend.sequoia.com/rtw/client/space-bookings/floors?taskId=%s" % task_id,
        headers=token_headers(token))
    return [(x["floorName"], x) for x in response["data"]["floors"] if x["status"] == "active"]


def get_spaces(token, adjective, task_id, floor_id, start_time, end_time):
    url = ("https://hrx-backend.sequoia.com/rtw/client/space-bookings/%s/spaces?taskId=%s&floorId=%s&startTime=%s"
           "&endTime=%s") % (
              adjective, task_id, floor_id, start_time, end_time)
    response = api_call(method='GET', url=url, headers=token_headers(token))
    return response["data"]["spaces"] or []


def reserve_space(token, task_id, start_time, end_time, space_id, user_id, reservation_id):
    response = api_call(method='POST', url="https://hrx-backend.sequoia.com/rtw/client/space-bookings/space",
                        headers=token_headers(token),
                        json={"taskId": task_id, "startTime": start_time, "endTime": end_time, "spaceId": space_id,
                              "userId": user_id, "reservationId": reservation_id}
                        )
    return response["data"]["label"]


def draw_floor_plan(floor, spaces):
    if 'blueprintUrl' not in floor:
        return
    spaces = [x for x in spaces if 'Rx' in x]
    if not spaces:
        return

    base_width = floor['baseWidth']
    aspect_ratio = floor["aspectRatio"]
    base_height = round(base_width * aspect_ratio)

    min_x = base_width
    min_y = base_height
    max_x = 0
    max_y = 0
    for space in spaces:
        x = space['Rx']
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        y = space['Ry']
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    new_width = (max_x - min_x)
    new_height = (max_y - min_y)

    w = min(FLOOR_PLAN_COLS, os.get_terminal_size()[0]) - FLOOR_PLAN_BUFFER
    h = round(w * (new_height / new_width) * TERMINAL_CHAR_ASPECT_RATIO)

    grid = []
    for _ in range(h + FLOOR_PLAN_BUFFER):
        grid.append([" "] * (w + FLOOR_PLAN_BUFFER))

    for space in spaces:
        x = round((space['Rx'] - min_x) / new_width * w)
        y = round((space['Ry'] - min_y) / new_height * h)
        color = space['color']
        grid[y][x] = "\033[%sm%s\033[0m" % (color, DOT)

    for row in grid:
        print("".join(row))
    print(
        "\033[%sm%s\033[0m preferred    "
        "\033[%sm%s\033[0m free    "
        "\033[%sm%s\033[0m booked by someone you are following    "
        "\033[%sm%s\033[0m booked" % (
            COLOR_PREFERRED, DOT, COLOR_AVAILABLE, DOT, COLOR_BOOKED_FOLLOWING, DOT, COLOR_BOOKED, DOT))


def get_space(token, task, floor, config, followings):
    floor_id = floor["floorId"]
    task_id = task["taskId"]
    start_time = task["reservationStartTime"]
    end_time = task["reservationEndTime"]
    available_spaces = get_spaces(token, "available", task_id, floor_id, start_time, end_time)
    default = None
    preferred_space_id = config.get("preferred_space_id")
    if not preferred_space_id:
        preferred_space_id = inquirer.text(message="Preferred space ID (press return for none)")
    all_spaces = []
    available_space_set = set()
    for available_space in available_spaces:
        available_space["color"] = COLOR_AVAILABLE
        space_id = available_space["spaceId"]
        unique_space_id = available_space["uniqueSpaceId"]
        if space_id == preferred_space_id:
            available_space["color"] = COLOR_PREFERRED
            default = unique_space_id
        all_spaces.append(available_space)
        available_space_set.add(unique_space_id)
    booked_spaces = get_spaces(token, "booked", task_id, floor_id, start_time, end_time)
    for booked_space in booked_spaces:
        space_id = booked_space["spaceId"]
        if space_id == preferred_space_id:
            default = booked_space["uniqueSpaceId"]
        full_name = "%s %s" % (booked_space.get("firstName"), booked_space.get("lastName"))
        booked_space["fullName"] = full_name
        booked_space["color"] = COLOR_BOOKED_FOLLOWING if full_name in followings else COLOR_BOOKED
        all_spaces.append(booked_space)
    all_spaces.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s["label"])])
    choices = []
    for space in all_spaces:
        raw_label = space["label"]
        color = space["color"]
        label: str = "\033[%sm%s\033[0m" % (color, raw_label)
        full_name = space.get("fullName")
        if full_name:
            label = "\033[%sm%s (%s)\033[0m" % (color, raw_label, full_name)
        choices.append((label, space["uniqueSpaceId"]))
    try:
        draw_floor_plan(floor, all_spaces)
    except Exception as e:
        print("Failed to draw floor plan: ", e)
    while True:
        unique_space_id = do_inquiry("Space", choices, default)
        if unique_space_id in available_space_set:
            return booked_spaces, unique_space_id
        print("Invalid selection")


def get_booking_map(bookings, space_id=-1):
    out = {}
    for booking in bookings:
        key = "%s %s" % (booking['firstName'], booking['lastName'])
        if space_id == booking["spaceId"]:
            key = YOU
        out[key] = booking['label']
    return out


def run_tasks(token, config, pending_task_ids, followings):
    out = {}
    for pending_task_id in pending_task_ids:
        task = get_task(token, pending_task_id)
        task_id = task["taskId"]
        task_metadata = task["taskMetadata"]
        task_data = task_metadata.get("data")
        card_info = task_metadata["cardInfo"]
        print("%s:\n\n\t%s %s %s\n\t%s\n\t%s\n" % (
            task["taskTitle"],
            card_info.get("displayTitle", ""),
            card_info.get("title", ""),
            card_info.get("heading", ""),
            card_info.get("basicSubtitle", ""),
            card_info.get("caption", "")
        ))
        if not task_data:
            floor_id = task.get("floorId")
            start_time = task.get("reservationStartTime")
            end_time = task.get("reservationEndTime")
            if floor_id and start_time and end_time:
                out = get_booking_map(get_spaces(token, "booked", task_id, floor_id, start_time, end_time),
                                      task.get("spaceId"))
            continue
        if not inquirer.confirm("Complete task?", default=True):
            continue
        questions = task_data["questions"]
        if not questions or not task_data["hasQuestionnaire"]:
            raise Exception("Task without questionnaire not supported")
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
        floor = do_inquiry("Floor", floors)
        (bookings, space_id) = get_space(token, task, floor, config, followings)
        start_time = task["reservationStartTime"]
        end_time = task["reservationEndTime"]
        user_id = task["recipientId"]
        reservation_id = task["reservationId"]
        space_label = reserve_space(token, task_id, start_time, end_time, space_id, user_id, reservation_id)
        print("You have booked '%s'" % space_label)
        out = get_booking_map(bookings)
        out[YOU] = space_label
    return out


def print_weeks(weeks, today, booked, followings, choices, current_spaces):
    rows = []
    for week in weeks:
        label = "WEEK OF %s" % week[0].strftime('%d %b').upper()
        header = [label]
        booking_row = [YOU]
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
        if current_spaces:
            header.append("Today's\nSpace" if today in week else "")
            booking_row.append(current_spaces.get(YOU, ""))
        for name, days in followings.items():
            user_row = [name]
            add_row = False
            for day in week:
                if day in days:
                    entry = CHECK_MARK
                    add_row = True
                else:
                    entry = ""
                user_row.append(entry)
            if current_spaces:
                space = current_spaces.get(name)
                if space and today in week:
                    user_row.append(space)
                else:
                    user_row.append("")
            if add_row:
                rows.append(user_row)
    t = Texttable(max_width=0)
    t.add_rows(rows, header=False)
    print(t.draw())


def run():
    try:
        from . import __version__
    except ImportError:
        __version__ = None
    version = "unknown" if not __version__ else "v%s" % __version__
    print("\U0001F332 \033[32mW A W O N A\033[0m \U0001F332\n\n%s - https://github.com/yuzawa-san/wawona\n" % version)
    config = get_config()
    token = get_token()
    try:
        pending_task_ids = get_pending_tasks(token)
    except ApiException:
        token = get_token(True)
        pending_task_ids = get_pending_tasks(token)
    today = date.today()
    weekday = today.weekday()
    if weekday < 5:
        start = today - timedelta(days=weekday)
    else:
        start = today + timedelta(days=7 - weekday)
    days = 14
    end = start + timedelta(days=days)
    booked = get_summary(token, start, end)
    followings = get_followings(token, start, end)
    current_spaces = run_tasks(token, config, pending_task_ids, followings)
    choices = []
    weeks = [[], []]
    for day_offset in range(days):
        day = start + timedelta(days=day_offset)
        weekday = day.weekday()
        if weekday < 5:
            weeks[day_offset // 7].append(day)
    print_weeks(weeks, today, booked, followings, choices, current_spaces)
    if not choices:
        return

    locations = get_locations(token)
    location = do_inquiry("Office", locations)

    questions = [
        inquirer.Checkbox(
            "dates",
            message="Date(s) to reserve (press return for none)",
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
    check_tasks = add_reservations(token, location, to_book, config)
    booked = get_summary(token, start, end)
    print_weeks(weeks, today, booked, {}, [], {})
    if check_tasks:
        for i in range(5):
            print("Waiting for pending tasks...")
            sleep(1)
            pending_task_ids = get_pending_tasks(token)
            if pending_task_ids:
                run_tasks(token, config, pending_task_ids, followings)
                return
        print("Unable to find pending tasks.")


if __name__ == "__main__":
    run()

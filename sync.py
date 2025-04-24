import os
import re
import httpx
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.environ["GOOGLE_CALENDAR_ID"]

# 오늘 기준 ±2개월 범위 계산
today = datetime.utcnow()
start_range = today - timedelta(days=60)
end_range = today + timedelta(days=60)
time_min = start_range.isoformat() + "Z"
time_max = end_range.isoformat() + "Z"

def get_gcal_service():
    with open("credentials.json", "w") as f:
        f.write(os.environ["GOOGLE_CREDS"])
    with open("token.json", "w") as f:
        f.write(os.environ["GOOGLE_TOKEN"])

    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("calendar", "v3", credentials=creds)

def fetch_caldav_events():
    url = os.environ["CALDAV_URL"]
    username = os.environ["CALDAV_USER"]
    password = os.environ["CALDAV_PASS"]

    report_body = f'''<?xml version="1.0" encoding="UTF-8"?>
    <c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
      <d:prop>
        <d:getetag/>
        <c:calendar-data/>
      </d:prop>
      <c:filter>
        <c:comp-filter name="VCALENDAR">
          <c:comp-filter name="VEVENT">
            <c:time-range start="{start_range.strftime('%Y%m%dT000000Z')}" end="{end_range.strftime('%Y%m%dT235959Z')}"/>
          </c:comp-filter>
        </c:comp-filter>
      </c:filter>
    </c:calendar-query>
    '''

    with httpx.Client(auth=httpx.BasicAuth(username, password)) as client:
        res = client.request(
            "REPORT",
            url,
            headers={
                "Content-Type": "application/xml",
                "Depth": "1",
                "User-Agent": "macOS/13.0.1 (CalendarAgent)"
            },
            content=report_body
        )

    soup = BeautifulSoup(res.text, "xml")
    calendar_datas = soup.find_all("cal:calendar-data")
    vevents = []

    for cdata in calendar_datas:
        matches = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", cdata.text, re.DOTALL)
        vevents.extend(matches)


    return vevents

def clean_uid(uid):
    return re.sub(r'[^a-z0-9\-]', '', uid.lower())

def parse_event(vevent):
    uid = clean_uid(re.search(r"UID:(.+)", vevent).group(1).strip())
    summary = re.search(r"SUMMARY:(.+)", vevent).group(1).strip()
    dtstart_raw = re.search(r"DTSTART(?:;TZID=[^:]+)?:([0-9T]+)", vevent).group(1)
    dtend_raw = re.search(r"DTEND(?:;TZID=[^:]+)?:([0-9T]+)", vevent).group(1)

    # 📍 LOCATION 파싱 (없을 수 있으니 예외처리)
    location_match = re.search(r"LOCATION:(.+)", vevent)
    location = location_match.group(1).strip() if location_match else ""

    def format_datetime(dt_str):
        if "T" in dt_str:
            dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
        else:
            dt = datetime.strptime(dt_str, "%Y%m%d")
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    return {
        'id': uid,
        'summary': summary,
        'location': location,  # ← ✅ 추가됨!
        'start': {'dateTime': format_datetime(dtstart_raw) + "+09:00", 'timeZone': 'Asia/Seoul'},
        'end': {'dateTime': format_datetime(dtend_raw) + "+09:00", 'timeZone': 'Asia/Seoul'}
    }

def get_caldav_uids(vevents):
    uids = []
    for v in vevents:
        raw_uid = re.search(r"UID:(.+)", v).group(1).strip()
        uid = clean_uid(raw_uid)
        uids.append(uid)
    return set(uids)

def get_google_event_uids(service):
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return {e['id']: e for e in events}

def delete_removed_events(service, gcal_events, caldav_uids):
    for gid in gcal_events.keys():
        if gid not in caldav_uids:
            try:
                service.events().delete(calendarId=CALENDAR_ID, eventId=gid).execute()
                print(f"🗑️ 삭제 완료: {gcal_events[gid]['summary']}")
            except Exception as e:
                print(f"⚠️ 삭제 실패: {gcal_events[gid]['summary']}\n{e}")

def main():
    service = get_gcal_service()
    vevents = fetch_caldav_events()

    caldav_uids = get_caldav_uids(vevents)
    gcal_events = get_google_event_uids(service)

    for v in vevents:
        event = parse_event(v)
        try:
            service.events().get(calendarId=CALENDAR_ID, eventId=event['id']).execute()
            service.events().update(calendarId=CALENDAR_ID, eventId=event['id'], body=event).execute()
            print(f"🔁 업데이트 완료: {event['summary']}")
        except Exception as e:
            if "notFound" in str(e):
                try:
                    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                    print(f"✅ 등록 완료: {event['summary']}")
                except Exception as insert_err:
                    print(f"⚠️ 등록 실패: {event['summary']}\n{insert_err}")
            else:
                print(f"⚠️ 실패: {event['summary']}\n{e}")

    delete_removed_events(service, gcal_events, caldav_uids)

if __name__ == "__main__":
    main()

# Python imports
import logging
from typing import Dict, Any
import time
import datetime

# 3rd party imports
import boto3
import pandas as pd
from bs4 import BeautifulSoup
import requests


def get_location_data(location):
    """
    Purpose:
        get location data from name
    Args:
        N/A
    Returns:
        N/A
    """

    # x — Specifies the x coordinate or longitude.
    # y — Specifies the y coordinate or latitude.
    client = boto3.client("location")

    response = client.search_place_index_for_text(
        IndexName="re_engage_places", Text=location
    )

    # print(response)
    geo_data = response["Results"][0]["Place"]["Geometry"]["Point"]

    lng = geo_data[0]
    lat = geo_data[1]

    print(f"{lat},{lng}")

    return lat, lng


def scrape_meetup_data(
    df_map: Dict[str, Any],
    time_now: datetime.datetime,
    meetup_url: str,
) -> None:
    """
    Purpose:
        get data for meetup
    Args:
        N/A
    Returns:
        dataframe of meetup data
    """

    logging.info(f"Getting info for {meetup_url}")

    # Get meetup info
    if "www.meetup.com" in meetup_url:

        try:
            meetup_info = get_meetup_info(meetup_url, time_now)
        except Exception as error:
            logging.error(error)
            return

        if meetup_info == None:
            return
        df_map["meetup_link"].append(meetup_url)
        meetup_location = meetup_info["meetup_location"]

        # Create final JSON
        df_map["state"].append(meetup_info["state"])
        df_map["meetup_name"].append(meetup_info["meetup_name"])
        df_map["meetup_location"].append(meetup_info["meetup_location"])
        df_map["meetup_members"].append(meetup_info["meetup_members"])
        df_map["num_past_events"].append(meetup_info["num_past_events"])
        df_map["last_event_time"].append(meetup_info["last_event_time"])
        df_map["last_event_timestamp"].append(meetup_info["last_event_timestamp"])
        df_map["is_meetup_active_3_months"].append(meetup_info["is_meetup_active_3"])
        df_map["is_meetup_active_6_months"].append(meetup_info["is_meetup_active_6"])
        df_map["is_meetup_active_12_months"].append(meetup_info["is_meetup_active_12"])

        try:
            lat, lng = get_location_data(meetup_location)
            df_map["latitude"].append(lat)
            df_map["longitude"].append(lng)
        except Exception as error:
            logging.error(error)
            logging.error("No lat long?")
            df_map["latitude"].append(0.0)
            df_map["longitude"].append(0.0)

    else:
        logging.warn("Invalid meetup link")


def get_user_group_data(usergroup_website: str) -> pd.DataFrame:
    """
    Purpose:
        get user group data
    Args:
        region: region
        usergroup_website: usergroup_website
    Returns:
        dataframe of user group data
    """

    # JSON map of data
    df_map = {}
    df_map["state"] = []
    df_map["meetup_link"] = []
    df_map["meetup_name"] = []
    df_map["meetup_location"] = []
    df_map["meetup_members"] = []
    df_map["num_past_events"] = []
    df_map["last_event_time"] = []
    df_map["last_event_timestamp"] = []
    df_map["is_meetup_active_3_months"] = []
    df_map["is_meetup_active_6_months"] = []
    df_map["is_meetup_active_12_months"] = []
    df_map["longitude"] = []
    df_map["latitude"] = []

    time_now = datetime.datetime.now()

    scrape_meetup_data(df_map, time_now, usergroup_website)

    df = pd.DataFrame.from_dict(df_map)
    return df


def get_meetup_info(meetup_url: str, now: datetime.datetime) -> Dict[str, Any]:
    """
    Purpose:
        get meetup info
    Args:
        meetup_url - url for the meetup
        now - current time
    Returns:
        meetup data
    """

    meetup_json = {}
    page = requests.get(meetup_url)
    usergroup_html = page.text
    soup = BeautifulSoup(usergroup_html, "html.parser")

    # Get Meetup Name
    try:
        meetup_name = soup.findAll("a", {"class": "groupHomeHeader-groupNameLink"})[
            0
        ].text
    except:

        return None

    # Meetup location
    meetup_location = soup.findAll("a", {"class": "groupHomeHeaderInfo-cityLink"})[
        0
    ].text

    # Number of members
    meetup_members = (
        soup.findAll("a", {"class": "groupHomeHeaderInfo-memberLink"})[0]
        .text.split(" ")[0]
        .replace(",", "")
    )

    # Past events
    try:
        past_events = (
            soup.findAll(
                "h3", {"class": "text--sectionTitle text--bold padding--bottom"}
            )[0]
            .text.split("Past events ")[1]
            .replace("(", "")
            .replace(")", "")
        )
    # Spanish?
    except:
        try:
            past_events = (
                soup.findAll(
                    "h3", {"class": "text--sectionTitle text--bold padding--bottom"}
                )[0]
                .text.split("Eventos anteriores ")[1]
                .replace("(", "")
                .replace(")", "")
            )
        except:
            past_events = 0
    # Date of last event

    try:
        last_event_timestamp = int(
            soup.findAll(
                "div",
                {
                    "class": "eventTimeDisplay text--labelSecondary text--small wrap--singleLine--truncate margin--halfBottom"
                },
            )[0]
            .find()
            .attrs["datetime"][0:-3]
        )
    except:
        return None
    local_event_time = time.strftime(
        "%a, %b %d %Y %H:%M:%S %Z", time.localtime(last_event_timestamp)
    )

    dt_object = datetime.datetime.fromtimestamp(last_event_timestamp)

    # Get date
    # Was last event > 3 months ago?
    delta = now - dt_object
    is_meetup_active_3 = True
    is_meetup_active_6 = True
    is_meetup_active_12 = True

    if delta.days > 90:
        is_meetup_active_3 = False
    if delta.days > 180:
        is_meetup_active_6 = False
    if delta.days > 360:
        is_meetup_active_12 = False
    # Last event online?

    # Create final JSON
    meetup_json["meetup_name"] = meetup_name
    meetup_json["meetup_location"] = meetup_location
    meetup_json["state"] = meetup_location.split(", ")[1]

    meetup_json["meetup_members"] = meetup_members
    meetup_json["num_past_events"] = past_events
    meetup_json["last_event_time"] = local_event_time
    meetup_json["last_event_timestamp"] = last_event_timestamp
    meetup_json["is_meetup_active_3"] = is_meetup_active_3
    meetup_json["is_meetup_active_6"] = is_meetup_active_6
    meetup_json["is_meetup_active_12"] = is_meetup_active_12

    print(meetup_json)

    return meetup_json


def main() -> None:
    """
    Purpose:
        Main script
    Args:
        N/A
    Returns:
        N/A
    """
    logging.info("Getting meetup data")

    # Pass in your meetup group URL
    curr_url = "https://www.meetup.com/amazon-web-services-virginia/"

    df = get_user_group_data(curr_url)

    # Get current time
    time_now = datetime.datetime.now()
    collected_time = time_now.strftime("%m_%d_%Y")

    # Save data to csv
    file_name = f"{collected_time}_meetup_data.csv"
    df.to_csv(file_name, index=False)


if __name__ == "__main__":
    loglevel = logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
    main()

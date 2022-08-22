# Meetup Scraper
This code provides a template to web scrape data from [Meetup](www.meetup.com) using python and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

## To run

Simply run, the following to start the script.

```bash
pip install -r requirements.txt
python collect_meetup_data.py
```

## Notes

Line 260 has a hardcoded URL for a meetup group, you are free to modify this input mechanism to collect data on whatever group you are looking for.  

Also line 86 invokes the `get_location_data` function which leverages AWS Location Service. Feel free to remove this if you don't need location data.

The output of the script is a CSV with the following fields.  
```
state,meetup_link,meetup_name,meetup_location,meetup_members,num_past_events,last_event_time,last_event_timestamp,is_meetup_active_3_months,is_meetup_active_6_months,is_meetup_active_12_months,longitude,latitude
```

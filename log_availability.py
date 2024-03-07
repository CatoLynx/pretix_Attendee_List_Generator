import csv
import requests
import time

from config import *


def api_call(path, method='get', payload=None):
    if path.startswith(API_URL):
        url = path
    else:
        url = API_URL + path
    
    if method == 'get':
        resp = requests.get(url, headers={"Authorization": "Token " + API_TOKEN})
    elif method == 'post':
        resp = requests.post(url, data=payload, headers={"Authorization": "Token " + API_TOKEN})
    return resp


def main():
    from pprint import pprint
    availability = {}
    
    print("Getting quotas")
    data = {'next': f"organizers/{ORGANIZER}/events/{EVENT}/quotas"}
    resp = api_call(data['next'])
    if resp.status_code != 200:
        print(f"  Error: HTTP status code {resp.status_code}")
        return
    data = resp.json()
    fieldnames = ["Time"] + [quota['name'] for quota in data['results']] + ["Orders"]
    
    i = 0
    with open("availability.csv", 'w') as f:
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        while True:
            print("Getting quotas")
            data_quotas = {'next': f"organizers/{ORGANIZER}/events/{EVENT}/quotas?with_availability=true"}
            
            while data_quotas['next']:
                print(f"  Querying {data_quotas['next']}")
                resp = api_call(data_quotas['next'])
                availability["Time"] = time.time()
                if resp.status_code != 200:
                    print(f"  Error: HTTP status code {resp.status_code}")
                    break
                
                data_quotas = resp.json()
                quotas = data_quotas['results']

                for quota in quotas:
                    availability[quota['name']] = quota['available_number'] or 0
            
            if i % 10 == 0:
                print("Getting orders")
                url = f"organizers/{ORGANIZER}/events/{EVENT}/orders?page_size=1"
                print(f"  Querying {url}")
                resp = api_call(url)
                if resp.status_code != 200:
                    print(f"  Error: HTTP status code {resp.status_code}")
                    break
                data_orders = resp.json()
                availability["Orders"] = data_orders['count']
            
            writer.writerow(availability)
            print(availability)
            i += 1


if __name__ == "__main__":
    main()

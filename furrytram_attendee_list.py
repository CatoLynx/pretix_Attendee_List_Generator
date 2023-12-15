import requests
from lxml import etree
from lxml.html import fragment_fromstring

from config import *


def api_call(path, method='get', payload=None):
    if method == 'get':
        resp = requests.get(API_URL + path, headers={"Authorization": "Token " + API_TOKEN})
    elif method == 'post':
        resp = requests.post(API_URL + path, data=payload, headers={"Authorization": "Token " + API_TOKEN})
    return resp


def main():
    print("Getting orders")
    resp = api_call(f"organizers/{ORGANIZER}/events/{EVENT}/orders")
    if resp.status_code != 200:
        print(f"  Error: HTTP status code {resp.status_code}")
        return
    
    orders = resp.json()['results']
    
    att_list = []
    att_list_no_consent = []
    html = ""

    for order in orders:
        # Skip non-paid orders
        if order['status'] != 'p':
            continue
        positions = order['positions']
        for position in positions:
            answered = False
            for answer in position['answers']:
                if answer['question'] == CONSENT_QUESTION_ID:
                    answered = True
                    if answer['answer'] == "True":
                        att_list.append(position['attendee_name'])
                    else:
                        att_list_no_consent.append(position['attendee_name'])
            if not answered:
                att_list_no_consent.append(position['attendee_name'])
    
    if not att_list:
        att_list = ["..."]
    
    att_list.sort(key=str.casefold)
    att_list_no_consent.sort(key=str.casefold)

    print("\n\nAttendee List:")
    for attendee in sorted(att_list, key=str.casefold):
        print("  " + attendee)
    
    print("\n\nNo consent:")
    for attendee in sorted(att_list_no_consent, key=str.casefold):
        print("  " + attendee)
    
    print("\n\nUpdating HTML files")
    for filename in OUTPUT_FILES:
        # Read file
        with open(filename, 'r') as f:
            page = f.read()
        
        # Parse and get HTML node
        tree = etree.HTML(page)
        node = tree.xpath(f'//*[@id="{ATT_LIST_HTML_ID}"]')[0]
        
        # Delete content
        for child in node.getchildren():
            node.remove(child)
        
        # Add new content
        for att_name in att_list:
            content = fragment_fromstring(f"<li>{att_name}</li>")
            node.append(content)
        
        # Write file
        with open(filename, 'wb') as f:
            f.write(etree.tostring(tree))


if __name__ == "__main__":
    main()

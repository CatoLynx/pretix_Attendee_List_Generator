import requests
import unicodedata
from lxml import etree
from lxml.html import fragment_fromstring

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
    att_list = []
    att_list_no_consent = []
    
    print("Getting orders")
    data = {'next': f"organizers/{ORGANIZER}/events/{EVENT}/orders"}
    
    while data['next']:
        print(f"  Querying {data['next']}")
        resp = api_call(data['next'])
        if resp.status_code != 200:
            print(f"  Error: HTTP status code {resp.status_code}")
            return
        
        data = resp.json()
        orders = data['results']

        for order in orders:
            # Skip non-paid orders
            if order['status'] != 'p':
                continue
            positions = order['positions']
            for position in positions:
                if position.get('attendee_name') is None:
                    continue
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
    
    def _sortfun(s):
        # Strip accents, then casefold
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn').casefold()
    
    att_list.sort(key=_sortfun)
    att_list_no_consent.sort(key=_sortfun)

    print("\n\nAttendee List:")
    for attendee in att_list:
        print("  " + attendee)
    
    print("\n\nNo consent:")
    for attendee in att_list_no_consent:
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

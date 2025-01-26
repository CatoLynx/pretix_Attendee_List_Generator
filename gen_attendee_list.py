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
    
    print("Getting waiting list entries")
    data = {'next': f"organizers/{ORGANIZER}/events/{EVENT}/waitinglistentries"}
    
    waiting_list_count = 0
    while data['next']:
        print(f"  Querying {data['next']}")
        resp = api_call(data['next'])
        if resp.status_code != 200:
            print(f"  Error: HTTP status code {resp.status_code}")
            return
        
        data = resp.json()
        entries = data['results']

        for entry in entries:
            if entry['voucher'] is None:
                waiting_list_count += 1
    
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
            # Skip cancelled orders
            if order['status'] == 'c':
                continue
            
            # Skip non-paid orders if desired
            if SHOW_ONLY_PAID_ORDERS and order['status'] != 'p':
                continue
            
            positions = order['positions']
            for position in positions:
                if position.get('attendee_name') is None:
                    continue
                
                att_list_entry = {'name': None, 'fursuiter': None}
                addons = [pos for pos in positions if pos.get('addon_to') == position['id']]
                
                for addon in addons:
                    if addon['item'] == FURSUITER_ITEM_ID:
                        if addon['variation'] == FURSUITER_FULL_VARIATION_ID:
                            att_list_entry['fursuiter'] = 'full'
                        elif addon['variation'] == FURSUITER_PARTIAL_VARIATION_ID:
                            att_list_entry['fursuiter'] = 'partial'
                
                answered = False
                for answer in position['answers']:
                    if answer['question'] == CONSENT_QUESTION_ID:
                        answered = True
                        if answer['answer'] == "True":
                            att_list_entry['name'] = position['attendee_name']
                            #print(att_list_entry)
                            att_list.append(att_list_entry.copy())
                        else:
                            att_list_no_consent.append(position['attendee_name'])
                if not answered:
                    att_list_no_consent.append(position['attendee_name'])
    
    if not att_list:
        att_list = [{'name': "...", 'fursuiter': None}]
    
    def _sortfun(s):
        # Strip accents, then casefold
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn').casefold()
    
    att_list.sort(key=lambda e: _sortfun(e['name']))
    att_list_no_consent.sort(key=_sortfun)

    print(f"\n\nWaiting list count: {waiting_list_count}")

    print("\n\nAttendee List:")
    for attendee in att_list:
        if attendee['fursuiter'] == 'full':
            fursuit_tag = "[F]"
        elif attendee['fursuiter'] == 'partial':
            fursuit_tag = "[P] "
        else:
            fursuit_tag = "[ ]"
        print("  " + fursuit_tag, attendee['name'])
    
    print("\n\nNo consent:")
    for attendee in att_list_no_consent:
        print("  " + attendee)
    
    print("\n\nUpdating HTML files")
    for filename in OUTPUT_FILES:
        # Read file
        with open(filename, 'r') as f:
            page = f.read()
        
        # Parse and get attendee list HTML node
        tree = etree.HTML(page)
        node = tree.xpath(f'//*[@id="{ATT_LIST_HTML_ID}"]')[0]
        
        # Delete content
        for child in node.getchildren():
            node.remove(child)
        
        # Add new content
        for att_data in att_list:
            if att_data['fursuiter'] == 'full':
                fursuit_tag = "[F]"
            elif att_data['fursuiter'] == 'partial':
                fursuit_tag = "[P] "
            else:
                fursuit_tag = "[ ]"
            content = fragment_fromstring(f"<li>{fursuit_tag} {att_data['name']}</li>")
            node.append(content)
        
        if WAITING_LIST_INFO_HTML_ID is not None:
            # Parse and get waiting list info HTML node
            node = tree.xpath(f'//*[@id="{WAITING_LIST_INFO_HTML_ID}"]')[0]
            
            # Set visibility
            node.set('style', '' if waiting_list_count > 0 else 'display: none;')
        
        if WAITING_LIST_COUNT_HTML_ID is not None:
            # Parse and get waiting list count HTML node
            node = tree.xpath(f'//*[@id="{WAITING_LIST_COUNT_HTML_ID}"]')[0]
            
            # Set content
            node.text = str(waiting_list_count)
        
        # Write file
        with open(filename, 'wb') as f:
            f.write(etree.tostring(tree))


if __name__ == "__main__":
    main()

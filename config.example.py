# Pretix API base url, with protocol and trailing slash
API_URL = "https://pretix.example.com/api/v1/"

# Pretix API token
API_TOKEN = "abcdefg"

# Pretix organizer ID
ORGANIZER = "johndoe"

# Pretix event ID
EVENT = "awesome-event"

# List of HTML files that should be updated
OUTPUT_FILES = ["/var/www/index.html", "/var/www/index_en.html"]

# HTML ID of the ul or ol element that should be populated with li children for the attendees
ATT_LIST_HTML_ID = "att-list"

# Numerical ID of the question in pretix that asks the user for consent to be listed publicly on the website
CONSENT_QUESTION_ID = 1

# Numerical ID of the item in pretix equivalent to a fursuiter
FURSUITER_ITEM_ID = 2

# Numerical IDs of the product variants in pretix equivalent to fursuit variants
FURSUITER_FULL_VARIATION_ID = 1
FURSUITER_PARTIAL_VARIATION_ID = 2
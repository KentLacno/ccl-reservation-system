# Constants for the reservation system

# Weekdays mapping
WEEKDAYS = {
    "1": "monday",
    "2": "tuesday", 
    "3": "wednesday",
    "4": "thursday",
    "5": "friday"
}

WEEKDAY_CHOICES = (
    ("1", "monday"),
    ("2", "tuesday"),
    ("3", "wednesday"),
    ("4", "thursday"),
    ("5", "friday"),
)

# Payment constants
PAYMONGO_SERVICE_FEE_RATE = 0.025
PESO_TO_CENTAVOS_MULTIPLIER = 100

# OAuth scopes
MICROSOFT_OAUTH_SCOPES = ["User.Read", "profile", "email", "openid"]

# Organization domain
ALLOWED_EMAIL_DOMAIN = "cclcentrex.edu.ph"

# URLs
MICROSOFT_AUTH_BASE_URL = 'https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize'
MICROSOFT_TOKEN_URL = 'https://login.microsoftonline.com/organizations/oauth2/v2.0/token'
MICROSOFT_GRAPH_USER_URL = "https://graph.microsoft.com/v1.0/me?$select=displayName,givenName,jobTitle,mail,department,id"
PAYMONGO_CHECKOUT_URL = "https://api.paymongo.com/v1/checkout_sessions"

# Random password length
RANDOM_PASSWORD_LENGTH = 32 
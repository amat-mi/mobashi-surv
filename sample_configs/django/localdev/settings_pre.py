RUNENV="localdev"
DEBUG=True
IS_DEVELOPMENT_MACHINE=True

#Add here any possible legitimate origin (wildcard do NOT work with credentials too) 
CORS_ALLOWED_ORIGIN_REGEXES = [
  r"^http://localhost.*$",            
]

# CSRF_TRUSTED_ORIGINS = [
#   "localhost",             #comment out when not needed for debugging
# ]

from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = (
    *default_headers,
    'origin',
    'accept-encoding',
)

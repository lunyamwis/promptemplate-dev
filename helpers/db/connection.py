# your_code.py

from django.db import connections
from product.models import DatabaseCredential, Company

def connect_to_external_database(company: Company):
    # Retrieve credentials from the DatabaseCredential model
    credentials = DatabaseCredential.objects.get(company=company)

    # Dynamically create a new database connection
    connections.databases[company.name] = {
        'ENGINE': credentials.engine,  # Adjust the engine based on your database type
        'NAME': credentials.database,
        'USER': credentials.user,
        'PASSWORD': credentials.password,
        'HOST': credentials.host,
        'PORT': int(credentials.port),
        'TIME_ZONE': 'UTC',
        'CONN_HEALTH_CHECKS': False, 
        'CONN_MAX_AGE': 0,
        'OPTIONS': {},
        'ATOMIC_REQUESTS': False, 
        'AUTOCOMMIT': True,
        'CHECKS': False,
    }


SAML2_AUTH_CONFIG = {
    # Using default remote backend
    "AUTHENTICATION_BACKEND": "django.contrib.auth.backends.RemoteUserBackend",
    # Metadata is required, choose either remote url or local file path
    "METADATA_AUTO_CONF_URL": "https://login.microsoftonline.com/{AZURE_TENANT_ID}/federationmetadata/2007-06/federationmetadata.xml?appid={AZURE_APP_ID}",
    "ENTITY_ID": "https://demo.peering-manager.net",
}

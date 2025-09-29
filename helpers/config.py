"""Module for general configurations of the process"""

# ----------------------
# Workqueue settings
# ----------------------
MAX_RETRY = 1

# ----------------------
# Queue population settings
# ----------------------
MAX_CONCURRENCY = 10  # tune based on backend capacity
MAX_RETRIES = 1  # failure retries per item
RETRY_BASE_DELAY = 0.5  # seconds

# ----------------------
# Data config setup
# ----------------------
MODERSMAAL_CONFIG = {
    "os2_webform_id": "tilmelding_til_modersmaalsunderv",
    "excel_file_name": "Dataudtræk - monday_last_week til sunday_last_week.xlsx",
    "folder_name": "General",
    "site_name": "Teams-Modersmlsundervisning",
    "formular_mapping": {
        "serial": "Serial number",
        "created": "Oprettet",
        "completed": "Gennemført",
        "elevens_navn_mitid": "Elevens navn",
        "elevens_cpr_nummer_mitid": "Elevens CPR-nummer",
        "elevens_adresse_mitid": "Elevens adresse",
        "mit_barn_kommer_ikke_frem_i_listen": "Mit barn kommer ikke frem i listen",
        "elevens_navn": "Elevens navn - manuelt",
        "cpr_elevens_nummer": "Elevens CPR-nummer - manuelt",
        "elevens_adresse": "Elevens adresse - manuelt",
        "klassetrin": "Klassetrin",
        "hvilken_type_skole_gaar_dit_barn_paa": "Hvilken type skole går dit barn på?",
        "skole_kommunal_api": "Skole API NR",
        "skole": "Skole",
        "oensket_sprog": "Ønsket sprog",
        "har_eleven_tidligere_modtaget_modersmaalsundervisning_": "Har eleven tidligere modtaget modersmålsundervisning?",
        "hvis_ja_antal_aar_01": "Hvis ja, antal år",
        "navn_foraeldre_01": "Forælders navn",
        "cpr_nummer_foraeldre_01": "Forælders CPR-nummer",
        "adresse_foraeldre_01": "Forælders adresse",
        "kommunekode": "Kommunekode",
        "foraeldres_e_mail": "Forælders e-mail",
        "telefonnummer_foraelder": "Forælders telefonnummer",
        "statsborgerskab": "Forælders statsborgerskab",
        "navn_foraeldre_02": "Partners/Medforælders navn",
        "e_mail_foraelder_02": "Partners/Medforælders e-mail",
        "telefonnummer_foraelder_02": "Partners/Medforælders telefonnummer",
        "statsborgerskab_medforaelder": "Partners/Medforælders statsborgerskab",
    },
}

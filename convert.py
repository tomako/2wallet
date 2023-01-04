import os
from argparse import ArgumentParser
from csv import DictReader, DictWriter
from codecs import BOM_UTF8, BOM_UTF16_LE, BOM_UTF16_BE, BOM_UTF32_LE, BOM_UTF32_BE
from typing import Optional

NBSP = '\xa0'

BOOKING_DATE_EN = 'Booking Date'
BOOKING_DATE_HU = 'Könyvelés dátuma'
AMOUNT_EN = 'Amount'
AMOUNT_HU = 'Összeg'
CURRENCY_EN = 'Currency'
CURRENCY_HU = 'Devizanem'
PARTNER_NAME_EN = 'Partner Name'
PARTNER_NAME_HU = 'Partner név'
SENDER_REFERENCE_EN = 'Sender Reference'
SENDER_REFERENCE_HU = 'Megbízás azonosító'
BOOKING_INFO_EN = 'Booking Info'
BOOKING_INFO_HU = 'Könyvelési információk'
NARRATIVE_EN = 'Narrative'
NARRATIVE_HU = 'Közlemény'
TRANSACTION_TYPE_EN = 'Transaction Type'
TRANSACTION_TYPE_HU = 'Tranzakció típusa'
TRANSACTION_DATETIME_EN = 'Transaction Date Time'
TRANSACTION_DATETIME_HU = 'Tranzakció dátuma és ideje'
NOTE_EN = 'Note'

TRANSLATION_MAP = ['en', 'hu']
TRANSLATIONS = ((BOOKING_DATE_EN, BOOKING_DATE_HU),
                (AMOUNT_EN, AMOUNT_HU),
                (CURRENCY_EN, CURRENCY_HU),
                (PARTNER_NAME_EN, PARTNER_NAME_HU),
                (SENDER_REFERENCE_EN, SENDER_REFERENCE_HU),
                (BOOKING_INFO_EN, BOOKING_INFO_HU),
                (NARRATIVE_EN, NARRATIVE_HU),
                (TRANSACTION_TYPE_EN, TRANSACTION_TYPE_HU),
                (TRANSACTION_DATETIME_EN, TRANSACTION_DATETIME_HU))

REQUIRED_FIELDS_EN = [BOOKING_DATE_EN, AMOUNT_EN, CURRENCY_EN, PARTNER_NAME_EN,
                      BOOKING_INFO_EN, NARRATIVE_EN, TRANSACTION_TYPE_EN, TRANSACTION_DATETIME_EN]
REQUIRED_FIELDS_HU = [BOOKING_DATE_HU, AMOUNT_HU, CURRENCY_HU, PARTNER_NAME_HU,
                      BOOKING_INFO_HU, NARRATIVE_HU, TRANSACTION_TYPE_HU, TRANSACTION_DATETIME_HU]
OUTPUT_FIELDS = [BOOKING_DATE_EN, AMOUNT_EN, CURRENCY_EN, PARTNER_NAME_EN, NOTE_EN]


def create_translation_dict(source_lang, target_lang='en'):
    source_lang_idx = TRANSLATION_MAP.index(source_lang)
    target_lang_idx = TRANSLATION_MAP.index(target_lang)
    return {translation[target_lang_idx]: translation[source_lang_idx] for translation in TRANSLATIONS}


def get_file_encoding(filename: str) -> Optional[str]:
    with open(filename, 'rb') as f:
        first_bytes = f.read(4)
        for enc, boms in (('utf-8-sig', (BOM_UTF8,)),
                          ('utf-32', (BOM_UTF32_LE, BOM_UTF32_BE)),
                          ('utf-16', (BOM_UTF16_LE, BOM_UTF16_BE))):
            if any(first_bytes.startswith(bom) for bom in boms):
                return enc


def transform_row(row: dict, dictionary: dict) -> dict:
    new_row = {}
    for field in OUTPUT_FIELDS:
        if field == NOTE_EN:
            new_row[NOTE_EN] = f'{row[dictionary[NARRATIVE_EN]]} ' \
                               f'{"Trn.type: " + (row[dictionary[TRANSACTION_TYPE_EN]] or "-")} ' \
                               f'{"Trn.date: " + (row[dictionary[TRANSACTION_DATETIME_EN]] or "-")} ' \
                               f'{"S.ref.: " + (row[dictionary[BOOKING_INFO_EN]] or "-")}'
        elif field == AMOUNT_EN:
            new_row[field] = row[dictionary[field]].replace(NBSP, '')
        else:
            new_row[field] = row[dictionary[field]]

    # post-actions
    if not new_row[PARTNER_NAME_EN]:
        new_row[PARTNER_NAME_EN] = 'Erste Bank'
    return new_row


def transform_csv(csv_input_file: str, csv_output_file: str) -> None:
    print(f'{csv_input_file} -> {csv_output_file}')
    with open(csv_input_file, encoding=get_file_encoding(csv_input_file)) as csv_in:
        csv_reader = DictReader(csv_in)
        if REQUIRED_FIELDS_EN[0] in csv_reader.fieldnames:
            translation_from = 'en'
            if not set(REQUIRED_FIELDS_EN) <= set(csv_reader.fieldnames):
                print(f'ERROR: Missing {translation_from} fields {set(REQUIRED_FIELDS_EN) - set(csv_reader.fieldnames)}')
                return
        elif REQUIRED_FIELDS_HU[0] in csv_reader.fieldnames:
            translation_from = 'hu'
            if not set(REQUIRED_FIELDS_HU) <= set(csv_reader.fieldnames):
                print(f'ERROR: Missing {translation_from} fields {set(REQUIRED_FIELDS_HU) - set(csv_reader.fieldnames)}')
                return
        else:
            print(f'Unknown language or incorrect fieldnames {set(csv_reader.fieldnames)}')
            return
        translation_dict = create_translation_dict(translation_from)
        with open(csv_output_file, mode='w', encoding='utf-8') as csv_out:
            csv_writer = DictWriter(csv_out, fieldnames=OUTPUT_FIELDS)
            csv_writer.writeheader()
            for row in csv_reader:
                csv_writer.writerow(transform_row(row, translation_dict))


if __name__ == '__main__':
    parser = ArgumentParser('Transform Erste CSV to be Wallet friendly')
    parser.add_argument('input_file', help='ERSTE CSV input file')
    args = parser.parse_args()
    if os.path.isfile(args.input_file):
        output_file = '{}_w{}'.format(*os.path.splitext(args.input_file))
        transform_csv(args.input_file, output_file)
    else:
        print('ERROR: Missing CSV input file')

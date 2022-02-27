import os
from argparse import ArgumentParser
from csv import DictReader, DictWriter
from codecs import BOM_UTF8, BOM_UTF16_LE, BOM_UTF16_BE, BOM_UTF32_LE, BOM_UTF32_BE
from typing import Optional

NBSP = '\xa0'

BOOKING_DATE = 'Booking Date'
BOOKING_DATE_HU = 'Könyvelés dátuma'
AMOUNT = 'Amount'
AMOUNT_HU = 'Összeg'
CURRENCY = 'Currency'
CURRENCY_HU = 'Devizanem'
PARTNER_NAME = 'Partner Name'
PARTNER_NAME_HU = 'Partner név'
SENDER_REFERENCE = 'Sender Reference'
SENDER_REFERENCE_HU = 'Megbízás azonosító'
NARRATIVE = 'Narrative'
NARRATIVE_HU = 'Közlemény'
TRANSACTION_TYPE = 'Transaction Type'
TRANSACTION_TYPE_HU = 'Tranzakció típusa'
NOTE = 'Note'

TRANSLATION_MAP = ['en', 'hu']
TRANSLATIONS = ((BOOKING_DATE, BOOKING_DATE_HU),
                (AMOUNT, AMOUNT_HU),
                (CURRENCY, CURRENCY_HU),
                (PARTNER_NAME, PARTNER_NAME_HU),
                (SENDER_REFERENCE, SENDER_REFERENCE_HU),
                (NARRATIVE, NARRATIVE_HU),
                (TRANSACTION_TYPE, TRANSACTION_TYPE_HU))

REQUIRED_FIELDS = [BOOKING_DATE, AMOUNT, CURRENCY, PARTNER_NAME,
                   SENDER_REFERENCE, NARRATIVE, TRANSACTION_TYPE]
REQUIRED_FIELDS_HU = [BOOKING_DATE_HU, AMOUNT_HU, CURRENCY_HU, PARTNER_NAME_HU,
                      SENDER_REFERENCE_HU, NARRATIVE_HU, TRANSACTION_TYPE_HU]
OUTPUT_FIELDS = [BOOKING_DATE, AMOUNT, CURRENCY, PARTNER_NAME, NOTE]


def create_dictionary(source_lang, target_lang='en'):
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
        if field == NOTE:
            new_row[NOTE] = f'{row[dictionary[NARRATIVE]]} ' \
                            f'{"Trn.type: " + (row[dictionary[TRANSACTION_TYPE]] or "-")} ' \
                            f'{"S.ref.: " + (row[dictionary[SENDER_REFERENCE]] or "-")}'
        elif field == AMOUNT:
            new_row[field] = row[dictionary[field]].replace(NBSP, '')
        else:
            new_row[field] = row[dictionary[field]]

    # post-actions
    if not new_row[PARTNER_NAME]:
        new_row[PARTNER_NAME] = 'Erste Bank'
    return new_row


def transform_csv(csv_input_file: str, csv_output_file: str) -> None:
    print(f'{csv_input_file} -> {csv_output_file}')
    with open(csv_input_file, encoding=get_file_encoding(csv_input_file)) as csv_in:
        csv_reader = DictReader(csv_in)
        if set(REQUIRED_FIELDS) <= set(csv_reader.fieldnames):
            translation_from = 'en'
        elif set(REQUIRED_FIELDS_HU) <= set(csv_reader.fieldnames):
            translation_from = 'hu'
        else:
            print(f'ERROR: Missing fields {set(REQUIRED_FIELDS) - set(csv_reader.fieldnames)}')
            return
        dictionary = create_dictionary(translation_from)
        with open(csv_output_file, mode='w', encoding='utf-8') as csv_out:
            csv_writer = DictWriter(csv_out, fieldnames=OUTPUT_FIELDS)
            csv_writer.writeheader()
            for row in csv_reader:
                csv_writer.writerow(transform_row(row, dictionary))


if __name__ == '__main__':
    parser = ArgumentParser('Transform Erste CSV to be Wallet friendly')
    parser.add_argument('input_file', help='ERSTE CSV input file')
    args = parser.parse_args()
    if os.path.isfile(args.input_file):
        output_file = '{}_w{}'.format(*os.path.splitext(args.input_file))
        transform_csv(args.input_file, output_file)
    else:
        print('ERROR: Missing CSV input file')

import pandas as pd
import numpy as np
import pymysql
import os
import re
import math
import json
import shutil
import time
import sys
from tqdm import tqdm
import random
from datetime import datetime
from pathlib import Path
from env import env, tokens
from twilio.rest import Client
import tkinter as tk
from tkinter import filedialog

twilio_account_sid = tokens.twilio_env['twilio_account_sid']
twilio_auth_token = tokens.twilio_env['twilio_auth_token']
twilio_phone_number = tokens.twilio_env['twilio_phone_number']
to_phone_number = tokens.twilio_env['to_phone_number']

twilio_client = Client(twilio_account_sid, twilio_auth_token)

segment_mapping = {
    'SF/HQ': ('JAKARTA', 'DKI JAKARTA'),
    'SF/BDG': ('BANDUNG', 'JAWA BARAT'),
    'SF/SKB': ('SUKABUMI', 'JAWA BARAT'),
    'SF/CJR': ('CIANJUR', 'JAWA BARAT'),
    'SF/TSM': ('TASIKMALAYA', 'JAWA BARAT'),
    'SF/TGR': ('TANGERANG', 'BANTEN'),
    'SF/BGR': ('BOGOR', 'JAWA BARAT'),
    'SF/SRG': ('SERANG', 'BANTEN'),
    'SF/SBG': ('SUBANG', 'JAWA BARAT'),
    'SF/CRB': ('CIREBON', 'JAWA BARAT'),
    'SF/BJR': ('BANJARNEGARA', 'JAWA TENGAH'),
    'SF/LBK': ('LEBAK', 'BANTEN'),
    'SF/PKL': ('PEKALONGAN', 'JAWA TENGAH'),
    'SF/PMK': ('PAMEKASAN', 'JAWA TIMUR'),
    'SF/PNR': ('PONOROGO', 'JAWA TIMUR'),
    'SF/MLG': ('MALANG', 'JAWA TIMUR'),
    'SF/SLO': ('SOLO', 'JAWA TENGAH'),
    'SF/BJN': ('BOJONEGORO', 'JAWA TIMUR'),
    'SF/LMG': ('LAMONGAN', 'JAWA TIMUR'),
    'SF/KDR': ('KEDIRI', 'JAWA TIMUR'),
    'SF/LMJ': ('LUMAJANG', 'JAWA TIMUR'),
    'SF/TGL': ('TEGAL', 'JAWA TENGAH'),
    'SF/SMG': ('SEMARANG', 'JAWA TENGAH'),
    'SF/KDS': ('KUDUS', 'JAWA TENGAH'),
    'SF/GBG': ('GROBOGAN', 'JAWA TENGAH'),
    'SF/MDN': ('MADIUN', 'JAWA TIMUR'),
    'SF/JBR': ('JEMBER', 'JAWA TIMUR'),
    'SF/SBY': ('SURABAYA', 'JAWA TIMUR'),
    'SF/PWT': ('PURWOKERTO', 'JAWA TIMUR'),
    'SF/DIY': ('YOGYAKARTA', 'DAERAH ISTIMEWA YOGYAKARTA'),
}

magic_loading_texts = [
    "Performing dark magic. Sit tight",
    "Performing magic on it",
    "Conjuring code mysteries...",
    "Weaving digital spells...",
    "Summoning computational powers...",
    "Casting bytes into spells...",
    "Unleashing arcane algorithms...",
    "Enchanting the data streams...",
    "Channeling virtual energies...",
    "Brewing a digital potion...",
    "Mystifying the machine...",
    "Invoking cyber sorcery...",
    "Decrypting mystical secrets...",
    "Activating wizardry protocols...",
    "Harnessing magical bytes...",
    "Entwining tech with magic...",
    "Orchestrating an ethereal symphony...",
    "Manipulating the fabric of code...",
    "Crafting a spellbinding process...",
    "Melding magic with mechanics...",
    "Weaving a web of wonders...",
    "Infusing magic into circuits...",
    "Shaping the mystical matrix...",
    "Engaging in digital alchemy...",
    "Transmuting data into magic...",
    "Evoking the spirits of silicon...",
    "Drawing power from the ether(net)...",
    "Enchanting the binary realm...",
    "Whispers of wizardry in progress...",
    "Dancing with digital demons...",
    "Stirring the cauldron of creativity...",
    "Unraveling the runes of programming..."
]

def select_file_or_folder(prompt):
    root = tk.Tk()
    root.withdraw()
    print(prompt)
    return filedialog.askopenfilename()

def update_env_file(env_paths):
    with open("env/env.py", 'w') as f:
        f.write(f"insert = {json.dumps(env_paths, indent=4)}\n")


def bold(text):
    return f"\033[1m{text}\033[0m"

def extract_segment(inv_number, channel):
    if channel == 'panel':
        parts = inv_number.split('/')
        if len(parts) > 3:
            return '/'.join(parts[2:4])
        return None
    elif channel == 'smr':
        parts = inv_number.split('/')
        smr_index = parts.index('SMR') + 1
        segment = parts[smr_index]
        if not parts[smr_index + 1].startswith('23'):# It's a compound segment, add the next part to the segment
            segment += '/' + parts[smr_index + 1]
        return segment
    
def new_customer(url):
    df = pd.read_csv(url)
    df = df[['Date','ID','Nama Pelanggan','Alamat','Kota','Provinsi','Kode pos','Telepon']]
    df['Telepon'] = df['Telepon'].astype(str).str.replace('.0','').str.replace('nan','')
    df['Date'].ffill(inplace=True)
    df['Kode pos'] = df['Kode pos'].fillna('')
    df['Nama Pelanggan'] = df['Nama Pelanggan'].str.strip()
    df = df.fillna('')
    df.drop_duplicates(subset=['ID'], inplace=True)
    
    with open(customer_names_json) as f:
        data = json.load(f)
    
    values_list = []
    for index, row in df.iterrows():
        if row['ID'] not in data:
            new_customer_name = row['Nama Pelanggan'].replace('\u00a0', ' ')
            data[row['ID']] = new_customer_name
            print(f"New customer added: {new_customer_name}")
            values_list.append((row['ID'], new_customer_name, row['Alamat'], row['Kota'], row['Provinsi'], row['Kode pos'], row['Telepon'], '', ''))
        else:
            continue

    with open(customer_names_json, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    if values_list:
        query = 'INSERT INTO customer(customer_id, customer_name, customer_address, regency, province, postal_code, customer_contact, customer_pic, customer_email) VALUES ' + ','.join([str(v) for v in values_list])
        return query
    else:
        print('No new customer found')
        return None

def insert_new_customer(query):
    host = env.db_config['host']
    user = env.db_config['user']
    password = env.db_config['password']
    database = env.db_config['database']

    connection = pymysql.connect(host=host, user=user, password=password, db=database)
    with connection.cursor() as cursor:
        cursor.execute(query)
    connection.commit()
    connection.close()

def clean(datapath):

    header = [
    'inv_number',
    'po_number',
    'channel',
    'customer_id',
    'customer_name',
    'order_time',
    'po_expired',
    'term_payment',
    'sales_name',
    'note'
]

    combined = pd.DataFrame(columns=header)

    if 'SMR_JKT_DIY' in datapath:
        print('Cleaning SMR data\n')
        smr = pd.read_excel(datapath, sheet_name='SMR_JKT_DIY')
        smr = smr[['No. Pesanan', 'Tgl Pesan', 'No. PO', 'No. Pelanggan', 'Nama Pelanggan', 'Nama Penjual', 'Name Syarat Pembayaran']]
        smr.rename(columns={'No. Pesanan': "inv_number", 'Tgl Pesan': "order_time", 'No. PO': 'po_number', 'No. Pelanggan': 'customer_id', 'Nama Pelanggan': "customer_name", 'Nama Penjual': "sales_name", 'Name Syarat Pembayaran': 'term_payment',}, inplace=True)
        smr.drop_duplicates(subset=['inv_number'], inplace=True)
        smr['po_expired'] = ''
        smr['channel'] = 'smr'
        smr['note'] = ''
        smr.fillna('', inplace=True)
        smr = smr[['inv_number','po_number','channel','customer_id','customer_name','order_time','po_expired','term_payment','sales_name','note']]
        
        combined = pd.concat([combined, smr], ignore_index=True)

    elif 'INV Panel.xlsx' in datapath:
        print('Cleaning INV Panel data\n')
        panel = pd.read_excel(panel_path, sheet_name='tb_panel')
        panel = panel[['No Faktur', 'Administration Time', 'Customer Id', 'Customer Name', 'Term Payment', 'Sales Name', 'Po Expired', 'Keterangan']]
        panel.rename(columns={'No Faktur': "inv_number", 'Administration Time': "order_time", 'Customer Id': 'customer_id', 'Customer Name': "customer_name",'Term Payment': 'term_payment', 'Sales Name': "sales_name", 'Po Expired': 'po_expired', 'Keterangan': 'note'}, inplace=True)
        panel.drop_duplicates(subset=['inv_number'], inplace=True)
        # convert po_expired into YYYY-MM-DD format
        panel['po_expired'] = pd.to_datetime(panel['po_expired'], format='%d %b %Y')
        panel['channel'] = 'panel'
        panel['po_number'] = ''
        # replace note with '' if its 0
        panel['note'] = panel['note'].replace(0, '')
        panel = panel[['inv_number','po_number','channel','customer_id','customer_name','order_time','po_expired','term_payment','sales_name','note']]

        combined = pd.concat([combined, panel], ignore_index=True)
    else:
        print('Invalid dataset\n')

    return combined

def process(data):
    df = data.copy()
    results = pd.DataFrame()
    count = len(results)
    if df['channel'].iloc[0] == 'smr':
        time_input =  pd.Timestamp.now().strftime('%H:%M:%S')
        df['order_time'] = pd.to_datetime(df['order_time'], format='%d %b %Y')
        df['order_time'] = df['order_time'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_smr, 'r') as file:
            segments_start_code = json.load(file)

        new_segments = False

        for inv_number in tqdm(df['inv_number'].unique(), desc='Processing segments'):
            segment = extract_segment(inv_number, 'smr')

            if not segment:
                continue

            if segment not in segments_start_code:
                print(f"\nNew segment found: {segment}. Adding with start code '0001'\n")
                segments_start_code[segment] = '0001'
                new_segments = True
        
        if new_segments:
            with open(start_code_smr, 'w') as file:
                json.dump(segments_start_code, file, indent=4)

        for segment, startcode in tqdm(segments_start_code.items(), desc='Processing segments'):
            try:
                pattern = f"/SMR/({segment}/|{segment}$)"
                segment_match = df['inv_number'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue
                
                segment_entry = df.loc[matched_rows[0], 'inv_number']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and month for segment {segment}. Skipping\n")
                    continue

                start_range = f"SO/SMR/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['inv_number'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue

                results = pd.concat([results, result])

                used_codes = result['inv_number'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}\n")
                continue
        
        with open(start_code_smr, 'w') as file:
            json.dump(segments_start_code, file, indent=4)

    elif data['channel'].iloc[0] == 'panel':
        time_input = pd.Timestamp.now().strftime('%H:%M:%S')
        df['order_time'] = pd.to_datetime(df['order_time'], format='%d %b %Y')
        df['order_time'] = df['order_time'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_panel, 'r') as file:
            segments_start_code = json.load(file)

        new_segments = False

        for inv_number in tqdm(df['inv_number'].unique(), desc='Processing segments'):
            segment = extract_segment(inv_number, 'panel') 
            if not segment:
                continue

            if segment not in segments_start_code:
                print(f"\nNew segment found: {segment}. Adding with start code '0001'\n")
                segments_start_code[segment] = '0001'
                new_segments = True

        if new_segments:
            with open(start_code_panel, 'w') as file:
                json.dump(segments_start_code, file, indent=4)


        for segment, startcode in tqdm(segments_start_code.items(), desc='Processing segments'):
            try:
                pattern = f"INV/ASW/({segment}/|{segment}$)"
                segment_match = df['inv_number'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue    
                
                segment_entry = df.loc[matched_rows[0], 'inv_number']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and month for segment {segment}. Skipping\n")
                    continue

                start_range = f"INV/ASW/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['inv_number'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue

                results = pd.concat([results, result])

                used_codes = result['inv_number'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}\n")
                continue
        
        with open(start_code_panel, 'w') as file:
            json.dump(segments_start_code, file, indent=4)
        
    else:
        print('\nInvalid dataset\n')
    
    return results

def generate_query(data, customer_names, po_expire):
    missing_segment_file = env.insert['missing_segment']
    batch = 20

    if data.empty:
        print('\nNo data to be inserted\n')
        return None
    
    new_customer_query_values = []
    preorder_query_values = []
    validation_query_values = []
    full_query = ''

    if data['channel'].iloc[0] == 'smr':
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc='Generating queries'):
            customer_number = str(row['customer_id'])
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['order_time'])
            no_SO = '' if isinstance(row['inv_number'], float) and math.isnan(row['inv_number']) else row['inv_number']
            no_inv = no_SO.replace('SO', 'INV')
            no_po = '' if isinstance(row['po_number'], float) and math.isnan(row['po_number']) else row['po_number']
            customer_name = customer_name.strip().replace('\n', ' ').replace('\r', '')
            note_sanitized = row['note'].strip().replace('\n', ' ').replace('\r', '')

            if customer_name == '':
                customer_name = row['customer_name']
                if customer_name not in customer_names.values():
                    segment = extract_segment(no_inv, data['channel'].iloc[0])
                    print(f"\nExtracted segment for invoice number {no_inv}: {segment}\n")  # Debug print
                    regency, province = segment_mapping.get(segment, ('', ''))
                    print(f"\nRegency: {regency}, Province: {province} for segment {segment}\n")  # Debug print
                    if regency == '' and province == '':
                        with open(missing_segment_file, 'a') as f:
                            f.write(f"{customer_number}: {customer_name}\n")
                    customer_address = ''

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name,
                            customer_address,
                            regency,
                            province,
                        )
                    )
                    new_customer_query_values.append(new_customer_value)
                
                if customer_name not in customer_names.values():
                    customer_name = customer_name.replace('\u00a0', ' ')
                    customer_names[str(customer_number)] = customer_name
                    with open(customer_names_json, 'w', encoding='utf-8') as f:
                        json.dump(customer_names, f, indent=4)
                    print(f"\nAdded '{customer_name}' for customer number {customer_number} in customer_names.json\n")

                    po_expire[customer_name] = 7
                    with open(po_expire_json, 'w') as f:
                        json.dump(po_expire, f, indent=4)
                    print(f"\nUpdated po_expire.json with default value for '{customer_name}'\n")

            fat_random_minute = np.random.randint(1, 10)
            start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')
            finish_time = (pd.to_datetime(start_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')

            po_expire_value = po_expire.get(customer_name, 4)
            po_expired = order_time + np.timedelta64(po_expire_value, 'D')

            preorder_value = (
                "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
                    no_inv,
                    no_po,
                    'NON-PANEL',
                    customer_number,
                    customer_name,
                    order_time,
                    po_expired,
                    row['term_payment'].strip(),
                    row['sales_name'].strip(),
                    row['note'].strip()
                )
            )
            preorder_query_values.append(preorder_value)

            validation_value = (
                "('{}','{}','{}','{}','{}')".format(
                    no_inv,
                    start_time,
                    finish_time,
                    'Process',
                    ''
                )
            )
            validation_query_values.append(validation_value)

        if new_customer_query_values:
            print('\n\nNew customer found\n\n')
            new_customer_query = (
                "INSERT INTO customer (customer_id, customer_name, customer_address, regency, province) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            total_batches = (len(preorder_query_values) + batch - 1) // batch
            for i in range(0, len(preorder_query_values), batch):
                batch_value = preorder_query_values[i:i+batch]
                preorder_query = (
                    "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES {}"
                    .format(','.join(batch_value))
                )
                full_query += preorder_query + '\n\n'
                print(f"\nQuery {i//batch + 1} of {total_batches} generated successfully\n")
        
            if validation_query_values:
                total_batches = (len(validation_query_values) + batch - 1) // batch
                for i in range(0, len(validation_query_values), batch):
                    batch_value = validation_query_values[i:i+batch]
                    validation_query = (
                        "INSERT INTO validation (inv_number, start_check, finish_check, fat_status, note) VALUES {}".format(
                            ','.join(batch_value)
                        )
                    )
                    full_query += validation_query + '\n\n'
                    print(f"\nQuery {i//batch + 1} of {total_batches} generated successfully\n")

    elif data['channel'].iloc[0] == 'panel':
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc='Generating queries'):
            customer_number = str(row['customer_id'])
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['order_time'])
            no_inv = row['inv_number']
            no_po = ''
            po_expired = row['po_expired']

            if customer_name == '':
                customer_name = row['customer_name']
                if customer_name not in customer_names.values():
                    segment = extract_segment(no_inv, data['channel'].iloc[0])
                    print(f"\nExtracted segment for invoice number {no_inv}: {segment}\n")  # Debug print
                    regency, province = segment_mapping.get(segment, ('', ''))
                    print(f"\nRegency: {regency}, Province: {province} for segment {segment}\n")  # Debug print
                    if regency == '' and province == '':
                        with open(missing_segment_file, 'a') as f:
                            f.write(f"{customer_number}: {customer_name}\n")
                    customer_address = ''

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name,
                            customer_address,
                            regency,
                            province,
                        )
                    )
                    new_customer_query_values.append(new_customer_value)
                
                if customer_name not in customer_names.values():
                    customer_name = customer_name.replace('\u00a0', ' ')
                    customer_names[str(customer_number)] = customer_name
                    with open(customer_names_json, 'w', encoding='utf-8') as f:
                        json.dump(customer_names, f, indent=4)
                    print(f"\nAdded '{customer_name}' for customer number {customer_number} in customer_names.json\n")

                    po_expire[customer_name] = 7
                    with open(po_expire_json, 'w') as f:
                        json.dump(po_expire, f, indent=4)
                    print(f"\nUpdated po_expire.json with default value for '{customer_name}'\n")

            fat_random_minute = np.random.randint(1, 10)
            start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')
            finish_time = (pd.to_datetime(start_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')

            preorder_value = (
                "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
                    no_inv,
                    no_po,
                    'PANEL',
                    customer_number,
                    customer_name,
                    order_time,
                    po_expired,
                    row['term_payment'],
                    row['sales_name'],
                    row['note']
                )
            )
            preorder_query_values.append(preorder_value)

        if new_customer_query_values:
            new_customer_query = (
                "INSERT INTO customer (customer_id, customer_name, customer_address, regency, province) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            total_batches = (len(preorder_query_values) + batch - 1) // batch
            for i in range(0, len(preorder_query_values), batch):
                batch_value = preorder_query_values[i:i+batch]
                preorder_query = (
                    "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES {}".format(
                        ','.join(batch_value)
                    )
                )
                full_query += preorder_query + '\n\n'
                print(f"\nQuery {i//batch + 1} of {total_batches} generated successfully\n")
    else:
        print('\nInvalid dataset\n')
    
    return full_query

def insert(query):
    host = env.db_config['host']
    user = env.db_config['user']
    password = env.db_config['password']
    database = env.db_config['database']

    connection = pymysql.connect(host=host, user=user, password=password, db=database)
    messages = None

    try:
        query_lines = query.splitlines()
        count = 0
        with connection.cursor() as cursor:
            for i, line in tqdm(enumerate(query_lines), total=len(query_lines), desc="Executing queries"):
                if line.strip():  # Check if the line is not empty
                    try:
                        cursor.execute(line)
                        print(f"\nQuery {i+1} executed successfully\n")
                        count += 1
                    except Exception as e:
                        print(f"\nError executing Query {i+1}: {e}\n")  # Print detailed error
                        # messages = twilio_client.messages.create(
                        #     from_=twilio_phone_number,
                        #     body=f"Error executing query {i+1}: {e}",
                        #     to=to_phone_number
                        # )
        connection.commit()
        print("\nAll queries executed successfully\n")
        # messages = twilio_client.messages.create(
        #     from_=twilio_phone_number,
        #     body=f"Database has been updated.",
        #     to=to_phone_number
        # )
    except Exception as e:
        # messages = twilio_client.messages.create(
        #     from_=twilio_phone_number,
        #     body=f"Error executing queries: {e}",
        #     to=to_phone_number
        # )
        print("\nERROR IN DATABASE OPERATION: {}\n".format(e))
    finally:
        connection.close()
    
    # return messages

if __name__ == "__main__":

    update_env = input("Do you want to update the env file? (y/n): ")
    if update_env.lower() == 'y':
        from env.env import insert as env_insert
        new_env_path = {}
        for key in env_insert:
            prompt = f"Select file or folder for {key}: "
            new_env_path[key] = select_file_or_folder(prompt)
        update_env_file(new_env_path)
        print("env file updated successfully")

    print(bold('\n===============STARTING===============\n'))
    smr_path = env.insert['smr']
    panel_path = env.insert['panel']
    customer_names_json = env.insert['customer_names']
    start_code_smr = env.insert['start_code_smr']
    start_code_panel = env.insert['start_code_panel']
    po_expire_json = env.insert['po_expire']
    customer_url = f"https://docs.google.com/spreadsheets/d/1ZjeukSSxbYccdee2bYZl3ldZ4ib2PCJE66I-Q5RwNyM/gviz/tq?tqx=out:csv&sheet=Sheet1"

    print(bold('\n===============Updating customer credentials===============\n'))
    newcustomer = new_customer(customer_url)
    if newcustomer is not None:
        insert_new_customer(newcustomer)
    else:
        print("No new customer query to execute")


    print(bold('\n===============Loading customer names files===============\n'))
    with open(customer_names_json, 'r', encoding='utf-8') as f:
        customer_names = json.load(f)

    print(bold('\n===============Loading start code files===============\n'))
    with open(po_expire_json, 'r') as f:
        po_expire = json.load(f)

    print(bold('\n===============Starting loop===============\n'))
    try:
        while True:
            smr_exists = os.path.exists(smr_path)
            panel_exists = os.path.exists(panel_path)

            if smr_exists:
                print(f'\n{smr_path} file found, cleaning it\n')
                # message = twilio_client.messages.create(
                #     from_=twilio_phone_number,
                #     body=f"SMR file found, {random.choice(magic_loading_texts).lower()}",
                #     to=to_phone_number
                # )
                cleaned = clean(smr_path)
                print('\nProcessing cleaned file\n')
                processed = process(cleaned)

                if not processed.empty:
                    time.sleep(5)
                    print('\nGenerating query\n')
                    query = generate_query(processed, customer_names, po_expire)
                    if query is not None:
                        print('\nInserting query\n')
                        insert(query)
                
                print('\nMoving SMR file\n')
                shutil.move(smr_path, smr_path.replace('PANEL&SMR', 'PANEL&SMR/ORIGINAL'))

            if panel_exists:
                print(f'\n{panel_path} file found, cleaning it\n')
                # message = twilio_client.messages.create(
                #     from_=twilio_phone_number,
                #     body=f"PANEL file found, {random.choice(magic_loading_texts).lower()}",
                #     to=to_phone_number
                # )
                cleaned = clean(panel_path)
                print('\nProcessing cleaned file\n')
                processed = process(cleaned)

                if not processed.empty:
                    time.sleep(5)
                    print('\nGenerating query\n')
                    query = generate_query(processed, customer_names, po_expire)
                    if query is not None:
                        print('\nInserting query\n')
                        insert(query)

                print('\nMoving Panel file\n')
                shutil.move(panel_path, panel_path.replace('PANEL&SMR', 'PANEL&SMR/ORIGINAL'))

            if not smr_exists and not panel_exists:
                print(bold('\nNo files found. Waiting...'))
                now = datetime.now()
                current = now.strftime("%H:%M:%S")
                print(bold("Current Time ="), current)
                print(bold('To exit, press CTRL+C'))
                time.sleep(3)

    except KeyboardInterrupt:
        print('\nKEYBOARD INTERRUPT DETECTED. EXITING...')
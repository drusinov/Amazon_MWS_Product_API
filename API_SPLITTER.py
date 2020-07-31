import os
import re
import random
import pandas as pd
import sqlite3 as lite


def random_SKU_gen(existing):
    random_letter = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    random_str = ''

    for x in range(2):
        random_str = random_str + random.choice(random_letter)
    random_str = random_str + '-'
    for x in range(4):
        random_str = random_str + random.choice(random_letter)
    random_str = random_str + '-'
    for x in range(4):
        random_str = random_str + random.choice(random_letter)

    while random_str in existing:
        for x in range(2):
            random_str = random_str + random.choice(random_letter)
        random_str = random_str + '-'
        for x in range(4):
            random_str = random_str + random.choice(random_letter)
        random_str = random_str + '-'
        for x in range(4):
            random_str = random_str + random.choice(random_letter)

    return random_str


def source_code():
    # --------------------------------------------------------------------------------------------------------------- #
    sys_username = str(os.getenv('username'))

    filter_out_dir = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{0}\GRAB_FIL_UNITED\output\Filter_Output.csv'.format(
            sys_username)

    notComp_DB = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{0}\GRAB_FIL_UNITED\output\notComp_DB.csv'.format(sys_username)

    comp_all = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{0}\GRAB_FIL_UNITED\output\comp_all.csv'.format(sys_username)

    already_listed = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{0}\GRAB_FIL_UNITED\output\already_listed.csv'.format(
            sys_username)

    DB_path = 'C:\\Users\\{0}\\Google Drive\\Inventory\\Main.db'.format(sys_username)

    # GET ALL SKU'S FROM DB
    con = lite.connect(DB_path)
    cur = con.cursor()
    cur.execute(f"""SELECT SKU FROM items""")

    existing_sku = cur.fetchall()
    cur.execute(f"""SELECT ASIN FROM items""")
    existing_asins = cur.fetchall()
    con.close()

    sku_list = [sku[0] for sku in existing_sku]
    asins_list = [asin[0] for asin in existing_asins]

    # WRITE HEADERS
    head_db = 'ASIN,SKU,UPC,Store,SaleChan,Status\n'
    head_scrnsht = 'ASIN,SKU,UPC,Store,SaleChan,Status,URL\n'

    with open(notComp_DB, 'w', encoding='utf-8') as f:
        f.write(head_db)
    with open(comp_all, 'w', encoding='utf-8') as f:
        f.write(head_scrnsht)
    with open(already_listed, 'w', encoding='utf-8') as f:
        f.write(head_scrnsht)

    c = 0
    row_values_list = list()
    with open(filter_out_dir, 'r', encoding='utf-8') as f:
        data_in = [line.replace('\n', '') for line in f]

        for line in data_in:
            if c == 0:
                c += 1
            else:
                row_values = line.split(',')
                row_values_list.append(row_values)

    for row in row_values_list:
        print('\nRow: ' + str(c) + ' of ' + str(len(row_values_list)) + '    :::    - SPLITTER -')

        in_Row = row[0]
        in_ASIN = row[1]
        in_SKU = row[2]
        in_UPC = row[3]
        in_Store = row[4]
        in_SaleChan = row[5]
        in_Status = row[6]
        in_URL = row[7]
        in_URL_E = row[8]

        if '----' in in_SKU:
            SKU_gen = random_SKU_gen(sku_list)
            in_SKU = SKU_gen

        in_ASIN = in_ASIN.replace('?', '')
        if in_ASIN[0] == '0' or in_ASIN[0] == 0:
            in_ASIN_check = re.findall(r'[A-Za-z]+', in_ASIN)
            len_list = len(in_ASIN_check)
            if len_list == 0:
                in_ASIN = f'?{in_ASIN}'

        if in_ASIN in asins_list:
            print(f'ASIN {in_ASIN} is Already Listed!')
            l_write = ','.join([in_ASIN, in_SKU, in_UPC, in_Store, 'AmD', 'ALREADY_LISTED', in_URL_E])
            with open(already_listed, 'a', encoding='utf-8') as f:
                f.write(l_write)
            c += 1
            continue

        if 'notComp' in in_Status:  # WRITE notComp_DB FILE
            l_write = ','.join([in_ASIN, 'notCompToBCheckd', in_UPC, in_Store, 'AmD', 'ToBCheckd'])
            with open(notComp_DB, 'a', encoding='utf-8') as f:
                f.write(l_write + '\n')

        if 'active' in in_Status:  # WRITE comp_all FILE
            l_write = ','.join([in_ASIN, in_SKU, in_UPC, in_Store, 'AmD', 'AUTO_ALL', in_URL_E])
            with open(comp_all, 'a', encoding='utf-8') as f:  # WRITE comp_all FILE
                f.write(l_write + '\n')

        c += 1


if __name__ == "__main__":
    source_code()

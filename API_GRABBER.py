from mws import mws
import os
import re
import xml.etree.ElementTree as ET
import time

import API_FILTER_STABLE as FILTER
import API_SPLITTER as SPLITTER


def reg_it(text):
    changed = re.findall(r'.+}(\w+)\s*', str(text))
    return changed[0]


def xml_print(var):
    print(var.tag, var.attrib, var.text)


def source_code():
    sys_username = str(os.getenv('username'))

    global input_id_dir
    input_id_dir = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{0}\GRAB_FIL_UNITED\input\Input IDs.csv'.format(sys_username)

    global filter_in_dir
    filter_in_dir = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{0}\GRAB_FIL_UNITED\input\New Prices.csv'.format(sys_username)

    global red_brands
    global red_brands_dir
    red_brands_dir = \
        r'C:\Users\{0}\Google Drive\Python_Shared\DO_NOT_DELETE\RED_BRANDS.txt'.format(
            sys_username)

    with open(red_brands_dir, 'r') as f:
        red_brands = f.readlines()

    red_brands_str = ','.join(red_brands)
    red_brands = re.sub(r'[^,\w]', '', red_brands_str)
    red_brands = red_brands.lower()

    output_del = input('Do you want to delete the output file? [y/n]:   ')
    print('\n')

    header_in = 'Row,ASIN,SKU,UPC,Store,SaleChan,Status,URL,Price,URL_E\n'

    if str(output_del).lower() == 'y':
        with open(filter_in_dir, 'w', encoding='utf-8') as f:
            f.write(header_in)

    with open(input_id_dir, 'r', encoding="utf-8") as f:
        data = [line.replace('\n', '') for line in f]

    headers = data[0:1]
    data = data[1:]
    data_new = list()
    for row in data:
        row_value = row.split(',')
        brand_mpn = row_value[1]
        brand_read = brand_mpn.split('?')[1]
        if brand_read not in red_brands:
            data_new.append(row)
    data = data_new
    with open(input_id_dir, 'w') as f:
        f.write(headers[0] + '\n')
        f.write('\n'.join(data))

    del data_new

    upcs_list = [row.split(',')[0] for row in data]

    c = 1
    upc_big_list = list()
    upc_sub_list = list()
    for upc in upcs_list:
        if '?' in upc:
            upc = upc.split('?')[1]
        if c % 5 == 0:
            upc_sub_list.append(upc)
            upc_big_list.append(upc_sub_list)
            upc_sub_list = list()
            c = 1
            continue

        upc_sub_list.append(upc)
        c += 1

    upc_big_list.append(upc_sub_list)
    upcs_by_five = upc_big_list

    access_key = os.environ['MWS_ACCESS_KEY']
    seller_id = os.environ['MWS_ACCOUNT_ID']
    secret_key = os.environ['MWS_SECRET_KEY']
    marketplace_usa = os.environ['MWS_MARKETPLACE_ID']

    for five in upcs_by_five:
        products_api = mws.Products(access_key, secret_key, seller_id, region='US')
        products = ''
        OK = False
        while not OK:
            try:
                products = products_api.get_matching_product_for_id(
                    marketplaceid=marketplace_usa,
                    type_='UPC',
                    ids=five
                )
                OK = True
            except Exception as ex:
                print(ex)

        # View as XML
        products_as_xml = products.original

        # Write XML file
        with open('UPCs.xml', 'w', encoding='utf-8') as f:
            f.write(products_as_xml)

        root = ET.parse('UPCs.xml').getroot()
        for upc_xml in root:
            if 'ResponseMetadata' in upc_xml.tag:
                continue
            upc_out = upc_xml.attrib['Id']
            print(f'UPC: {upc_out}')

            asins_dict = {}
            asin_out = brand_out = mpn_out = title_out = items_count = product_cat = 'NONE'
            sales_rank = '99999999'
            for asin in upc_xml[0]:  # upc_xml[0][0] stands for UPC > Products >
                identifiers = asin[0]
                attribute_sets = asin[1][0]
                sales_rankings = asin[3]

                asin_out = identifiers[0][1].text
                # print(f'{" " * 2}ASIN: {asin_out}')

                for each in attribute_sets:

                    if reg_it(each) == 'Brand':
                        brand_out = each.text
                        # print(f'{" " * 4}BRAND: {brand_out}')

                    if reg_it(each) == 'NumberOfItems':
                        items_count = each.text
                        # print(f'{" " * 4}ITEMS_COUNT: {items_count}')

                    if reg_it(each) == 'PartNumber':
                        mpn_out = each.text
                        # print(f'{" " * 4}MPN: {mpn_out}')

                    if reg_it(each) == 'ProductGroup':
                        product_cat = each.text
                        # print(f'{" " * 4}PRODUCT_CAT: {product_cat}')

                    if reg_it(each) == 'Title':
                        title_out = each.text
                        # print(f'{" " * 4}TITLE: {title_out}')

                try:
                    sales_rank = sales_rankings[0][1].text
                except IndexError:
                    pass

                # print(f'{" " * 4}SALES_RANK: {sales_rank}')
                # print()

                asins_dict[asin_out] = {
                    'BRAND': brand_out,
                    'ITEMS_COUNT': items_count,
                    'MPN': mpn_out,
                    'PRODUCT_CAT': product_cat,
                    'TITLE': title_out,
                    'SALES_RANK': sales_rank
                }

            total_asins_found = len(asins_dict)

            best_asin = best_asin_attrib = 'NONE'
            best_rank_asin = '999999999'
            best_asin_dict = {}
            for asin_dict in asins_dict:
                listing_rank = asins_dict[asin_dict]['SALES_RANK']
                # listing_items = asins_dict[asin_dict]['ITEMS_COUNT']
                # if int(listing_items) > 1:
                #     continue
                """
                CHECK IN OUR DB IF THE ASIN IS ALREADY LISTED 
                """
                if int(listing_rank) <= int(best_rank_asin):
                    best_asin = asin_dict
                    best_asin_attrib = asins_dict[asin_dict]
                    best_rank_asin = asins_dict[asin_dict]['SALES_RANK']

            best_asin_dict[best_asin] = best_asin_attrib
            asin_w = brand_w = items_count_w = mpn_w = product_cat_w = title_w = sales_rank_w = ''
            for asin in best_asin_dict:
                asin_w = asin
                brand_w = best_asin_dict[asin]['BRAND']
                items_count_w = best_asin_dict[asin]['ITEMS_COUNT']
                mpn_w = best_asin_dict[asin]['MPN']
                product_cat_w = best_asin_dict[asin]['PRODUCT_CAT']
                title_w = best_asin_dict[asin]['TITLE']
                sales_rank_w = best_asin_dict[asin]['SALES_RANK']

            print(f'{" " * 2}ASIN: {asin_w}')
            print(f'{" " * 4}BRAND: {brand_w}')
            print(f'{" " * 4}ITEMS_COUNT: {items_count_w}')
            print(f'{" " * 4}MPN: {mpn_w}')
            print(f'{" " * 4}PRODUCT_CAT: {product_cat_w}')
            print(f'{" " * 4}TITLE: {title_w}')
            print(f'{" " * 4}SALES_RANK: {sales_rank_w}')

            print()

            for row in data:
                row_items = row.split(',')
                if upc_out in row_items[0]:
                    row_upc = row_items[0]
                    row_store = row_items[1]
                    row_price = row_items[2]
                    row_url = row_items[3]

            new_prices_line = f'"----------",{asin_w},"----------",' \
                              f'{row_upc},{row_store},"AmD","ToBCheckd",' \
                              f'"ASIN Results: {str(total_asins_found)}",{row_price},{row_url}\n'
            with open(filter_in_dir, 'a') as f:
                f.write(new_prices_line)


print('\n------------------ GRABBER STARTS ------------------\n')  # 1. GRABBER
source_code()  # 1. GRABBER

print('\n------------------ FILTER STARTS ------------------\n')  # 2. FILTER
FILTER.source_code()  # 2. FILTER

print('\n------------------ SPLITTER STARTS ----------------\n')  # 3. SPLITTER
SPLITTER.source_code()  # 3. SPLITTER

'''
----------------- '#' IN FRONT OF THE LINE TO COMMENT OUT ------------------------
- COMMENT OUT 1.             IF YOU NEED 2. AND 3. ONLY
- COMMENT OUT 1. AND 2.      IF YOU NEED 3. ONLY
- COMMENT OUT 2. AND 3.      IF YOU NEED 1. ONLY
'''

from mws import mws
import os
import re
import xml.etree.ElementTree as ET
import time


def reg_it(text):
    changed = re.findall(r'.+}(\w+)\s*', str(text))
    return changed[0]


def source_code():
    sys_username = str(os.getenv('username'))

    input_dir = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{1}\GRAB_FIL_UNITED\input\New Prices.csv'.format(
            sys_username, sys_username)

    global filter_out_dir
    filter_out_dir = \
        r'C:\Users\{0}\Google Drive\Python_Shared\In_Out_{1}\GRAB_FIL_UNITED\output\Filter_Output.csv'.format(
            sys_username, sys_username)

    header_out = 'Row,ASIN,SKU,UPC,Store,SaleChan,Status,URL,URL_E\n'
    with open(filter_out_dir, 'w', encoding="utf-8") as f:
        f.write(header_out)

    with open(input_dir, 'r', encoding="utf-8") as f:
        data = [line.replace('\n', '') for line in f]

    data = data[1:]
    asins_list = [row.split(',')[1] for row in data]

    c = 1
    asin_big_list = list()
    asin_sub_list = list()
    asins_dict = {}
    for asin in asins_list:
        if '?' in asin:
            asin = asin.replace('?', '')
        if c % 20 == 0:
            asin_sub_list.append(asin)
            asin_big_list.append(asin_sub_list)
            asin_sub_list = list()
            c = 1
            continue

        asin_sub_list.append(asin)
        c += 1

    asin_big_list.append(asin_sub_list)
    asins_by_twenty = asin_big_list

    access_key = os.environ['MWS_ACCESS_KEY']
    seller_id = os.environ['MWS_ACCOUNT_ID']
    secret_key = os.environ['MWS_SECRET_KEY']
    marketplace_usa = os.environ['MWS_MARKETPLACE_ID']

    for twenty in asins_by_twenty:
        # t0 = time.time()
        products_api = mws.Products(access_key, secret_key, seller_id, region='US')
        products = ''
        OK = False
        while not OK:
            try:
                products = products_api.get_lowest_offer_listings_for_asin(
                    marketplaceid=marketplace_usa,
                    asins=twenty,
                    condition='New',
                )
                OK = True
            except Exception as ex:
                print(ex)

        time.sleep(0.5)
        # MAXIMUM OF 36000 ASINS PER HOUR
        # t1 = time.time()
        # print(str(t1 - t0))

        # View as XML
        products_as_xml = products.original

        # Write XML file
        with open('ASINS.xml', 'w', encoding='utf-8') as f:
            f.write(products_as_xml)

        root = ET.parse('ASINS.xml').getroot()

        for asin_xml in root:
            if 'ResponseMetadata' in asin_xml.tag:
                continue
            asin_out = asin_xml.attrib['ASIN']
            print(f'ASIN: {asin_out}')

            fulfillment = 'Merchant'
            landed_price = '9999999'

            for offer in asin_xml[1][1]:  # asin_xml[1][1] - LIST OF ALL OFFERS

                qualifiers_xml = offer[0]
                fulfillment = qualifiers_xml[2].text
                if fulfillment == 'Amazon':
                    fulfillment = 'NONE'
                    continue

                price_xml = offer[3]
                landed_price = price_xml[0][1].text
                break

            print(f'    FULFILLMENT: {fulfillment}')
            print(f'    LANDED PRICE: {landed_price}')
            print()

            asins_dict[asin_out] = landed_price

    for row in data:
        row = row.split(',')

        in_Row = row[0]
        in_ASIN = row[1]

        check_in_ASIN = in_ASIN
        if '?' in check_in_ASIN:
            check_in_ASIN = check_in_ASIN.replace('?', '')

        in_SKU = row[2]
        in_UPC = row[3]
        in_Store = row[4]
        in_SaleChan = row[5]
        in_URL = row[7]
        in_CalcPrice = round((float(row[8]) * 1.170), 2)
        in_URL_E = row[9]

        if float(in_CalcPrice) <= float(asins_dict[check_in_ASIN]):
            in_Status = 'active'
        else:
            in_Status = 'notComp'

        line_out = f'' \
                   f'{in_Row},{"?" + check_in_ASIN},{in_SKU},{in_UPC},' \
                   f'{in_Store},{in_SaleChan},{in_Status},' \
                   f'{in_URL},{in_URL_E}\n'

        with open(filter_out_dir, 'a') as f:
            f.write(line_out)


if __name__ == "__main__":
    source_code()

import base64
import datetime
import hashlib
import json
import re

# from geopy import Nominatim

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages


class Handler(Extract, GetPages):
    base_url = 'https://central3.to.gov.br'
    NICK_NAME = 'central3.to.gov.br'
    fields = ['overview']

    header = {
        'User-Agent':
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Mobile Safari/537.36',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7'
    }

    def get_by_xpath(self, tree, xpath, return_list=False):
        try:
            el = tree.xpath(xpath)
        except Exception as e:
            print(e)
            return None
        if el:
            if return_list:
                return [i.strip() for i in el]
            else:
                return el[0].strip()
        else:
            return None

    def check_tree(self, tree):
        print(tree.xpath('//text()'))

    def check_create(self, tree, xpath, title, dictionary, date_format=None):
        item = self.get_by_xpath(tree, xpath)
        if item:
            if date_format:
                item = self.reformat_date(item, date_format)
            dictionary[title] = item.strip()

    def getpages(self, searchquery):
        url = 'https://central3.to.gov.br/arquivo/390693/'
        tree = self.get_content(url, headers=self.header, stream=True)
        pdf = self.getpages_pdf(searchquery, 2, file_base_url=url, multiple_tables=True, stream=True)
        outList = []
        for i in range(3):
            # print(pdf[i].iloc[:3, :].to_string())
            # print(pdf[i].iloc[:, 1])
            res = pdf[i][pdf[i].iloc[:, 1].str.contains(searchquery)]#.to_string()
            if not res.empty:
                for (index_label, row_series) in res.iterrows():
                    for v in range(len(row_series.values)):
                        el = row_series.values[v]
                        #print(el)
                        #print('nan' not in str(el))
                        # if 'nan' not in str(el):
                        #     print(el)


                    name = row_series.values[1]
                    info = [str(k) for k in row_series.values[2:]]
                    info = [l for l in info if 'nan' not in l]
                    info = ' '.join(info)
                    outList.append(name +'?=' + str(i) + '?=' + info)
        return outList


    def reformat_date(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date



    def get_overview(self, link_name):
        comp_name = link_name.split('?=')[0]
        page = link_name.split('?=')[1]
        info = link_name.split('?=')[-1]
        company = {}
        try:
            orga_name = comp_name
        except:
            return None
        if orga_name: company['vcard:organization-name'] = orga_name.strip()
        company['isDomiciledIn'] = 'BR'
        company['hasActivityStatus'] = 'Inactive'
        dis_date = re.findall('\d\s*\d\s*\/\s*\d\s*\d\s*\/\s*\d\s*\d\s*\d\s*\d', info)
        if dis_date:
            info = info.replace(dis_date[0], '')
            company['dissolutionDate'] = self.reformat_date(dis_date[0].replace(' ',''), '%d/%m/%Y')
        lei = re.findall('\d\s*\d\s*\.\s*\d\s*\d\s*\d\s*\.\s*\d\s*\d\s*\d\s*\/\s*\d\s*\d\s*\d\s*\d\s*-\s*\d\s*\d', info)
        if lei:
            info = info.replace(lei[0], '')
            company['identifiers'] = {
                'vat_tax_number': lei[0].replace(' ', ''),
            }
        cla = ['SOCIEDADE EMPRESÁRIA LIMITADA', 'EMPRESÁRIO']
        form = re.findall('S\s*O\s*C\s*I\s*E\s*D\s*A\s*D\s*E.+', info)
        if not form:
            form = re.findall('E\s*M\s*P\s*R\s*E\s*S\s*Á\s*R\s*I\s*O.+', info)
            my_form = cla[1]
        else:
            my_form = cla[0]
        info = info.replace(form[0], '')
        company['lei:legalForm'] = {
            'code': '',
            'label': my_form
        }
        info = info.replace(' ', '')
        company['mdaas:RegisteredAddress'] = {
            'country': 'Brazil',
            'city': info.strip(),
            'fullAddress': info.strip() + ', Brazil'
        }
        company['@source-id'] = self.NICK_NAME

        return company
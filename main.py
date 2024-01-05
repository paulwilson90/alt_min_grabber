import pdfminer.utils
import requests
from html2text import html2text
import re
from io import BytesIO
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import json
import time
from convert_json import convert_to_json

start = time.time()


def collect_minima_data():
    """Will collect all location names and store in a list. For each airport in the list, it will collect
    the alt minima data.
    NB...Some locations will have low CATA/B minima and have been accounted for, these need to be checked each run.
    Typical CATA/B has a vis of 4.4, CAT C is 6.0 and CAT D is 7.0
    Run through the list and check if there are outliers.

    The print statement that is blocked out will give locations for items on the PDF chart if needed."""
    wipe = open('alternate_list.txt', 'w')
    wipe.write('')
    s = requests.session()
    page = s.get('https://www.airservicesaustralia.com/aip/current/dap/AeroProcChartsTOC.htm')
    tecst = html2text(page.text)

    airport_loc = re.findall(r'[(]Y\w\w\w[)]', tecst)
    for loc in airport_loc:
        exclude_lst = ['YATN', 'YATN', 'YUTA', 'YBSM', 'YBRB', 'YCLN', 'YPFT', 'YLBD', 'YUPA', 'YXGS', 'YIGM',
                       'YXLG', 'YXMA', 'YXMW', 'YXMO', 'YXFV', 'YPAM', 'YUPE', 'YSCF', 'YSBY', 'YTES', 'YTDN',
                       'YXTU', 'YWST', 'YWVR', 'YXWL', 'YWJL', 'YUOF']
        if loc[1:5] in exclude_lst:
            pass
        else:
            ap_id_loc = int(tecst.index(loc)) + 6
            ap_id_onward = tecst[ap_id_loc:]
            if loc == '(YYNG)':
                ap_id_to_nxt_ap = tecst[ap_id_loc:]
            else:
                next_loc = re.search(r'[(]Y\w\w\w[)]', ap_id_onward)
                next_loc_stop = tecst.index(next_loc.group())
                ap_id_to_nxt_ap = tecst[ap_id_loc:next_loc_stop]
            needed_text = (html2text(ap_id_to_nxt_ap))
            airport_id_less_Y = loc[2:5]

            app_1 = re.search(r'%sGN.*' % re.escape(airport_id_less_Y), needed_text)
            app_2 = re.search(r'%sII.*' % re.escape(airport_id_less_Y), needed_text)
            app_3 = re.search(r'%sVO.*' % re.escape(airport_id_less_Y), needed_text)
            if loc == '(YBCS)':
                line_o_chart = (app_1.group())
            elif loc == '(YPKG)':
                line_o_chart = (app_3.group())
            elif loc == '(YPPD)':
                line_o_chart = (app_3.group())
            else:
                try:
                    if app_2.group():
                        print(loc + " ILS")
                        line_o_chart = (app_2.group())
                except:
                    if app_1.group():
                        print(loc + " RNAV")
                        line_o_chart = (app_1.group())

            chart_title = (re.search(r'\w\w\w\w\w\d\d[-]\d*[_][\d\w]*[.]pdf', line_o_chart)).group()
            # getting exact pdf now
            chart_PDF = ('https://www.airservicesaustralia.com/aip/current/dap/' + chart_title)
            retrieve = s.get(chart_PDF)
            content = retrieve.content
            bytes = BytesIO(content)
            bytes.getbuffer()
            parser = PDFParser(bytes)
            document = PDFDocument(parser)
            # bypass the check for permission
            if not document.is_extractable:
                pass
            rsrcmgr = PDFResourceManager()
            device = PDFDevice(rsrcmgr)
            laparams = LAParams()
            devices = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, devices)
            # parse the pdf and extract text
            alt_line_lst = []

            def parse_obj(lt_objs):
                for obj in lt_objs:
                    if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
                        if round(obj.bbox[1]) >= 42 and round(obj.bbox[1]) <= 60:
                            if obj.bbox[0] < 300:
                                if loc == "(YWWI)":
                                    alt_line_lst.append(obj.get_text(
                                    ).replace('\n', '').replace(')', '').replace(' ', '-'))
                                else:
                                    alt_line_lst.append(obj.get_text().replace('\n', '').replace(' ', ''))
                        # print("%6d, %6d, %s" % (obj.bbox[0], obj.bbox[1], obj.get_text().replace('\n', '')))
                    elif isinstance(obj, pdfminer.layout.LTFigure):
                        parse_obj(obj._objs)

            for page in PDFPage.create_pages(document):
                interpreter.process_page(page)
                layout = devices.get_result()
                parse_obj(layout._objs)
            bytes.close()
            # sort the list of extracted text
            alt_line_lst = sorted(alt_line_lst)
            alternate_figs = re.findall(r'\d\d\d\d\s*[-]\s*\d[.]\d', ' '.join(alt_line_lst))
            alternate_figs = sorted(alternate_figs)
            for item in alternate_figs:
                # if loc == "(YTTI)":
                #     if int(item[:4]) <= 1090:
                #         alternate_figs.remove(item)
                if loc == "(YLRD)" or loc == "(YOLW)" or loc == "(YMIA)":
                    if int(item[:4]) <= 1069:
                        alternate_figs.remove(item)
                else:
                    if int(item[:4]) <= 1090:
                        alternate_figs.remove(item)
            with open('alternate_list.txt', 'a') as f:
                if loc == "(YBGD)":
                    f.write(loc + '["1250-4.4", "1580-6.0"]\n')
                elif loc == "(YCHK)":
                    f.write(loc + '["1186-4.4", "1306-6.0", "1306-7.0"]\n')
                elif loc == "(YGIA)":
                    f.write(loc + '["1101-4.4", "1331-6.0", "1431-7.0"]\n')
                elif loc == "(YMIA)":
                    f.write(loc + '["1173-4.4", "1233-6.0", "1313-7.0"]\n')
                else:
                    f.write(loc + json.dumps(alternate_figs) + '\n')


collect_minima_data()

end = time.time()
time_to_complete = end - start
round(time_to_complete, 2)
print(time_to_complete / 60, "minutes to complete")

convert_to_json()

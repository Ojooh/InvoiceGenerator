from __future__ import absolute_import, unicode_literals    
from celery import shared_task 
from .models import SwSearchMasterTbl,HazCustomerMasterTbl, SwInvoice
from configparser import ConfigParser
from celery import shared_task   
from datetime import datetime 
from django.utils import timezone
from django.conf import settings
import datetime as DT
import pdfkit
import shutil
import random
import os

# from pdf import PDFgenerator   
  
# @shared_task 
class InvoiceGenerator:

    # Init Method for invoice generator class
    def __init__(self, MasterTbl, UserTbl, CompanyTbl, ProductPricing, InvoiceTbl):
        """
            Function to initialize Invoice Generator Class
            set all model, array and dict fiels
            parameter 1     : Master Table Object
            parameter 2     : Customer Table Object
            parameter 3     : Comapny Table Object
            parameter 4     : Product Pricing Table Object 
            parameter 5     : Invoice Table Object   
        """
        self.invoice        = []
        self.done_user      = [] 
        self.master_tbl     = MasterTbl
        self.users          = UserTbl
        self.companys       = CompanyTbl
        self.invoiceT       = InvoiceTbl
        self.productP       = ProductPricing
        self.file_path       = os.path.join(os.path.dirname(settings.BASE_DIR), "files")
        self.file_path_1     = os.path.join(os.path.dirname(settings.BASE_DIR), "src", "static")
        self.products       = {'section66':'SWR66C', 'sewerServiceDiagram' : 'SWRSSD', 'serviceLocationPrint' : 'SWRSLP', 'buildingOverOrAdjacentToSewer' : 'SWRBOA', 'specialMeterReading' : 'SWRSMR', 'section88G' : 'SWR88G'}

    # Method to get search date from and to
    def setTransactionDate(self):
        # config_object = ConfigParser()

        # #Assume we need 2 sections in the config file, let's call them USERINFO and SERVERCONFIG
        # config_object["SEARCHDATE"] = {
        #     "from_date" : "2021-02-24 00:00:00",
        #     "to_date"   : "2021-02-25 00:00:00"
        # }

        # with open('config.ini', 'w+') as conf:
        #     config_object.write(conf)

        config_object       = ConfigParser()
        config_object.read("config.ini")
        today               = datetime.today()
        week_ago            = today - DT.timedelta(days=7)
        
        search_dates        = config_object["SEARCHDATE"]
        self.from_date      = datetime.strptime(search_dates["from_date"], "%Y-%m-%d %H:%M:%S")
        self.to_date        = datetime.strptime(search_dates["to_date"], "%Y-%m-%d %H:%M:%S")
        tz                  = timezone.get_current_timezone()

        if (self.from_date is not None and self.from_date != "") and (self.to_date is not None and self.to_date != ""):
            self.from_date           = timezone.make_aware(self.from_date, tz, True)
            self.to_date             = timezone.make_aware(self.to_date, tz, True)
            self.transactions         = self.master_tbl.objects.filter(order_datetime__range=[self.from_date, self.to_date])
            print(self.from_date)
            print(self.to_date)
            print(len(self.transactions))
            print(self.master_tbl.objects.filter(order_datetime__range=[self.from_date, self.to_date]).query)
        else :
            self.from_date           = timezone.make_aware(week_ago, tz, True)
            self.to_date             = timezone.make_aware(today, tz, True)
            self.transactions   = self.master_tbl.objects.filter(order_datetime__range=[self.from_date, self.to_date])
            print(len(self.transactions))
            print(self.master_tbl.objects.filter(order_datetime__range=[self.from_date, self.to_date]).query)


    # Method to generate unique invoice id
    def generate_invoice_id(self):
        """
            Function to generate a unique invoice ID based on 
            current date and the last id in the table
            returns invoice id
            
        """
        today               = datetime.today()
        today_string        = today.strftime('%y%m%d')
        next_invoice_number = '01'
        last_invoice        = self.invoiceT.objects.filter(invoice_id__startswith=today_string).order_by('invoice_id').last()
        if last_invoice:
            last_invoice_number = int(last_invoice.invoice_id[6:])
            next_invoice_number = '{0:02d}'.format(last_invoice_number + 1)
        invoice_id = today_string + next_invoice_number
        return invoice_id

    # Method to get invoice data fromdatabase and store in invoice array
    def get_invoice_data(self):
        """
            Function to extract invoice data from the models and store
            in an invoice array for every user
            returns invoice array
            
        """
        today                   = datetime.today()
        week_ago                = today - DT.timedelta(days=7)
        i                       = 0
        gst                     = 0

        for a in self.transactions:
            try:
                us = self.users.objects.get(customer_code=a.customer_code)
            except:
                us = None

            username = a.internal_username
            if username is not None:
                code = username.split("+")
                try:
                    comp = self.companys.objects.get(compcode=code[0])
                except:
                    comp = None
            else:
                comp = None

            try:
                idy     = a.product_name.strip()
                prd     = self.productP.objects.get(product_code=self.products[idy])
            except:
                prd = None

            
            
            if us != None and comp != None and prd != None:
            #if us != None and prd != None:
                
                if us.customer_name in self.done_user:
                    index           = self.done_user.index(us.customer_name)
                    realindex       = index + 1
                    realindex       = self.done_user[realindex]

                    rary            = self.invoice[realindex]
                    exist           = rary[len(rary) - 1]
                    # print(exist)
                    data    = {}

                    data["company_name"]                = comp.compname
                    data["cmpany_code"]                 = comp.compcode
                    data["cutomer_name"]                = us.customer_name
                    data["company_address"]             = comp.compstreet + " " + comp.compsuburb + " " + comp.compstate + " " + comp.comppostcode
                    data["phone"]                       = comp.compphone1
                    data["fax"]                         = comp.directfaxnumber
                    data["Searches_From"]               = self.from_date.strftime('%d/%m/%y')
                    data["Searches_To"]                 = self.to_date.strftime('%d/%m/%y')
                    data["Searches_No"]                 = a.haz_order_id
                    data["Search_Charge"]               = prd.sw_product_fees
                    data["Service_Charge"]              = prd.product_price
                    data["date_ordered"]                = a.order_datetime.strftime('%d/%m/%y')
                    data["reference"]                   = "Sydney Water Search"
                     # data["client_reference"]            = a.applicantreferencenumber
                    data["client_reference"]           = ""
                    data["disb"]                        = prd.sw_product_fees
                    data["charge"]                      = prd.product_price
                    data["disb_charge"]                 = prd.sw_product_fees + prd.product_price
                    data["disb_total"]                  = exist["disb_total"] + prd.sw_product_fees
                    data["charge_total"]                = exist["charge_total"] + prd.product_price
                    
                    # invoice number
                    data["last_payment_date"]           = ""
                    data["current_account_balance"]     = ""

                    if prd.product_gst_fees == "Yes":
                        gst      = 0.1 *  prd.product_price
                    else :
                        gst     = 0.1 * prd.sw_product_fees
                    data["GST_Charge"]                  = gst
                    data["disb_charge_total"]           = prd.sw_product_fees + prd.product_price + gst
                    data["total_price"]                 = prd.sw_product_fees + prd.product_price
                    data["disy"]                        = exist["disy"]  + prd.sw_product_fees + prd.product_price
                    data["GST_total"]                   = exist["GST_total"] + gst
                    data["disb_charge_totaly"]          = exist["disb_charge_totaly"] + prd.sw_product_fees + prd.product_price + gst

                    rary.append(data)
                    self.invoice[realindex] = rary

                else:    
                    self.done_user.append(us.customer_name)
                    self.done_user.append(i) 
                    usey                    = []
                    data                    = {}


                    data["invoice_id"]                  = self.generate_invoice_id()
                    data["company_name"]                = comp.compname
                    data["cmpany_code"]                 = comp.compcode
                    data["cutomer_name"]                = us.customer_name
                    data["company_address"]             = comp.compstreet + " " + comp.compsuburb + " " + comp.compstate + " " + comp.comppostcode
                    data["phone"]                       = comp.compphone1
                    data["fax"]                         = comp.directfaxnumber
                    data["Searches_From"]               = self.from_date.strftime('%d/%m/%y')
                    data["Searches_To"]                 = self.to_date.strftime('%d/%m/%y')
                    data["Searches_No"]                 = a.haz_order_id
                    data["Search_Charge"]               = prd.sw_product_fees
                    data["Service_Charge"]              = prd.product_price
                    data["date_ordered"]                = a.order_datetime.strftime('%d/%m/%y')
                    data["reference"]                   = "Sydney Water Search"
                    # data["client_reference"]            = a.applicantreferencenumber
                    data["client_reference"]           = ""
                    data["disb"]                        = prd.sw_product_fees
                    data["charge"]                      = prd.product_price
                    data["disb_charge"]                 = prd.sw_product_fees + prd.product_price
                    data["disb_total"]                  = prd.sw_product_fees
                    data["charge_total"]                = prd.product_price
                    

                    if prd.product_gst_fees == "Yes":
                        gst      = 0.1 *  prd.product_price
                    else :
                        gst     = 0.1 * prd.sw_product_fees
                    data["GST_Charge"]                  = gst
                    data["disb_charge_total"]           = prd.sw_product_fees + prd.product_price + gst
                    data["total_price"]                 = prd.sw_product_fees + prd.product_price
                    data["GST_total"]                   = gst
                    data["disy"]                        = prd.sw_product_fees + prd.product_price
                    data["disb_charge_totaly"]          = prd.sw_product_fees + prd.product_price + gst
                     # invoice number
                    data["last_payment_date"]           = ""
                    data["current_account_balance"]     = ""


                    usey.append(data)
                    self.invoice.append(usey)
                    i +=1
            else:
                continue
        
        print(self.done_user)
        return self.invoice

    # Method to generate pdf file and store in database from invoice array
    def invoice_generator(self, invoice_array, file_path):
        """
            Function to render a pdf file and save data in invoice datatbase
            parameter 1 : invoice array generated
            parameter 2 : path to create and store pdf file
            
        """ 
        table       = self.invoiceT()
        today       = datetime.today()
        week_ago    = today - DT.timedelta(days=7)
        t           = 0
        gst_total   = 0
        invoice_paths = []
        
        

        html_head   = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>TAX INVOICE</title><link rel="icon" href="/images/favicon.png" type="image/x-icon">
                        <style>body {font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;text-align: center;color: #777;margin: 0;padding: 0;}
                        body .wrapper {position: absolute;top: 0;left: 0;right: 0;max-width: 100%;height: 100%;margin: 0 auto;padding: 20px 30px;}
                        body .wrapper .top {display: inline;width: 100%;}
                        .top h3 {font-weight: 300;margin-top: 10px;margin-bottom: 20px;font-style: italic;color: rgb(48, 36, 100);float: left;}
                        .top h4 {font-weight: 300;margin-top: 10px;margin-bottom: 20px;font-style: italic;color: rgb(48, 36, 100);float: right;}
                        body a {color: #06F;}
                        .invoice-box {margin: 90px auto 20px auto;max-width: 1200px;padding: 20px;border: 1px solid #eee;box-shadow: 0 0 10px rgba(0, 0, 0, .15);font-size: 14px;line-height: 18px;font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;color: #555;height: auto;}
                        .invoice-box .invoice-box-top .container {display: table;height: 100%;width: 100%;}
                        .invoice-box .invoice-box-top {display: table;height: 100%;width: 100%;}
                        .invoice-box .invoice-box-top .col-lft-6 {display: table-cell;text-align: left;vertical-align: middle;width: 50%;padding: 1rem;}
                        .invoice-box .invoice-box-top .col-rght-6 {display: table-cell;text-align: right;vertical-align: middle;width: 50%;}
                        .invoice-box table {width: 100%;font-family: Arial, Helvetica, sans-serif;border-collapse: collapse;}
                        .invoice-box table td, .invoice-box table th {border: 1px solid #ddd;padding: 8px;}
                        .invoice-box table td {padding: 5px;vertical-align: top;color: #000;}
                        .invoice-box table td strong{font-weight: 600;}
                        .invoice-box table tr:nth-child(even){background-color: #f2f2f2}
                        .invoice-box table  tr:hover {background-color: #ddd;}
                        .invoice-box table th {padding-top: 12px;padding-bottom: 12px;text-align: left;background-color: #4CAF50;color: white;}
                        .invoice-box .total-summary {/* float: right; */text-align: right;}
                        .invoice-box .total-footer {/* float: right; */text-align: left;}
                        .invoice-box .abf-card {border: 5px solid #0e290f;padding: 20px;box-shadow: 0 10px 10px rgba(0, 0, 0, .15);border-radius: 10px;text-align: left;margin: 10px auto;}
                        .invoice-footer {text-align: center;line-height: 16px;margin: 30px auto;}
                        </style></head>"""
        html_1      = "<body><div class='wrapper'><div class='top'><h3>TAX INVOICE</h3><h4>Froms " + self.from_date + " to " + self.to_date + "</h3></div>"
        html_2      = ""

        # print(len(invoice_array))
        for invs in invoice_array:
            f               = 1
            file_name_1     = "sample-" + str(f) + ".html"
            file_name_2     = "invoice-" + str(f) + ".pdf"
            inv             = invs[0]
            date_from       = datetime.strptime(inv["Searches_From"], "%d/%m/%y")
            date_to         = datetime.strptime(inv["Searches_To"], "%d/%m/%y")
            date_from       = datetime.strftime(date_from, "%Y-%m-%d")
            date_to         = datetime.strftime(date_to, "%Y-%m-%d")
            #save to database First
            table.invoice_id      = inv["invoice_id"]
            table.company_name    = inv["company_name"] 
            table.cmpany_code     = inv["cmpany_code"]
            table.searches_from   = date_from
            table.searches_to     = date_to
            table.searches_no     = inv["Searches_No"]
            
            html_3          = "<div class='invoice-box'><div class=''><div class='invoice-box-top'><div class='col-lft-6'>" + "<h4>Account Name : " + inv["company_name"] + " </h4>""<h4>Address : " + inv["company_address"] + "</h4></div><div class='col-rght-6'>" + "<h4>Invoice Number : " + inv["invoice_id"] + " </h4>" +"<h4>Invoice Date : " + today.strftime('%d/%m/%y') + "</h4>" +"<h4>Phone : " + inv["company_address"] + "</h4>" + "<h4>Fax : " + inv["fax"] + "</h4></div></div></div>"

            html_4     = "<div class='container'><table cellpadding='0' cellspacing='0'><thead>" 
            html_5   = "<tr><th scope='col'>#</th><th scope='col'>Date Ordered</th>" +"<th scope='col'>Reference</th><th scope='col'>Client Reference</th><th scope='col'>Disb.</th>" + "<th scope='col'>Charge</th><th scope='col'>Disb. & Charge</th><th scope='col'>GST Amount</th>" + "<th scope='col'>Disb. & Charge (GST Inc.)</th></tr><tbody>"

        
            while t < len(invs):
                inv         = invs[t]
                gst_total   += inv["GST_Charge"]
                html_2 += "<tr><th scope='row'>" + str(t + 1) + "</th><td>"  +  inv["date_ordered"] + "</td><td>" + inv["reference"] + "</td><td>" + inv["client_reference"]  + "</td><td>" + str(inv["disb"]) + "</td><td>" + str(inv["charge"]) + "</td><td>" + str(inv["disb_charge"]) + "</td><td>" + str(inv["GST_Charge"])  + "</td><td>" + str(inv["disb_charge_total"])  + "</td>" 
                t = t + 1

            inv = invs[len(invs) - 1]
            html_6         = "</tbody></table></div><div class='container'><div class='total-summary'><h4>" +"Disb. & Charge : <strong>" + str(inv["disy"]) + "</strong></h4>" +"<h4> Taxes GST : " + str(inv["GST_total"]) + "</h4>" + "<h3> Total Invoice Amount : " + str(int(inv["disb_charge_totaly"])) + "</h3></div><hr>"

            html_7         = r'</div><div class="container"><div class="total-footer"><h4> <strong>Invoice Term : 7 Day Account</strong></h4><span><em>Please Note</em></h4><span><em>GST is calculated on the "Disb & Charge" for the supply</em></span><span><em>^1 Disb. is GST Exempt</em></span><span><em>^2 Disb. is GST Exempt</em></span><span><em>^3 Disb. & Charge are GST Exempt</em></span></div> </div> <div class="container"><div class="abf-card"> <p> Payment can be made via credit card or cheque. Please ensure the "invoice Number" is quoted when frwarding or completing all payments via CC, EFT OR CHQ. ie: 71083 </p> <p> <strong>Banking Details</strong> </p> <p> Name : R. Hazlett & Co<br> Bank : COMMONWEALTH BANK<br> BSB : 062021<br> Account : 10244749 </p> <p> <strong>CARD NUMBER</strong>_ _ _ _ _ _ _ _ _ _ _ __ _ _ _ _ _ _ _ _ _<br> <STRONG></STRONG> <strong>EXPIRY: _ _/_ _</strong> AMOUNT TO CHARGE : $__ __ </p> </div></div></div> <div class="container"><div class="invoice-footer"><img class="logo" src="' + self.file_path_1 + '\images\logo\logo.gif"<span>Lvel4, 122 Castleregah Street Sydney 200-DX 1078 SYDNEY<span><br></br><STRONG>GPO BOX 96 SYDNEY</STRONG><br> <span>phone : 926515211 Fax : 02 92647752</pspan <br><span> R Hazlett & co ABN 20 104 470 340</span><br><span>www.hazlett.com.au</span><br> </p></div></div></div></body></html>'


            print(file_name_1)
            with open(file_name_1,"w") as html:
                htm = html_head + html_1  + html_3 + html_4 +html_5 + html_2 + html_6 + html_7
                html.write(htm)
            
            
            pdfkit.from_file(file_name_1, file_name_2)
            shutil.copyfile(file_name_2, self.file_path_1 + "\\files\\" + file_name_2)
            invoice_paths.append(self.file_path_1 + "\\files" + file_name_2)
            new_folder      = random.randint(1,3910209312)
            final_folder    = '{path}\\{folder}'.format(path=self.file_path, folder=new_folder)
            if not os.path.exists(final_folder):
                os.makedirs(final_folder)
            shutil.move(file_name_2, final_folder)
            table.search_charge   = inv["disb_total"]
            table.service_charge  = inv["charge_total"]
            table.gst_charge      = inv["GST_total"]
            table.total_price     = inv["disb_charge_totaly"]
            table.pdf_link        = self.file_path + "\\" + file_name_2
            table.payment_status  = ""
            table.save()
            

            f += 1

        return invoice_paths

    # Caller method to execute all other methods
    def generate_invoice(self, file_path):
        """
            Function to execute Invoice Gneerator methods
            paramter 1 : file path to create or store pdf
            returns invoice array
            
        """

        print("Generating invoice.........")
        self.setTransactionDate()
        invoice_array   = self.get_invoice_data()

        if len(invoice_array) > 0 :
            paths = self.invoice_generator(invoice_array, file_path)
        else :
            paths = ""

        # return invoice_array
        return paths




# @shared_task  (name="test")  
# @shared_task(name="sum_two_numbers")
# def add(x, y):
#     return x + y
# @shared_task  (name="invoice_generate") 
# def start():
    
#     rary = InvoiceGenerator(SwSearchMasterTbl, HazCustomerMasterTbl, Company, SwProductPricing, SwInvoice)
#     rary.generate_invoice(file_path, file_path_1)     
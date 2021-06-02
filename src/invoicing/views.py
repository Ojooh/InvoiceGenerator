
import os, json
from .tasks import InvoiceGenerator
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from .models import *

def Welcome(request):
    return render(request, "welcome.html")

def Invoice(request):
    data = {}
    file_path   = os.path.join(os.path.dirname(settings.BASE_DIR), "files")
    rary        = InvoiceGenerator(SwSearchMasterTbl, HazCustomerMasterTbl, Company, SwProductPricing, SwInvoice)
    result      = rary.generate_invoice(file_path)

    if result != "": 
        data["success"]    = "Invoice Generated"
        data["paths"]       = result
    else:
        data["error"] = "Could not generate Invoice From Database, Important Fields were Null"

    return JsonResponse(data)
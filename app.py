from shutil import copyfile
from flask.globals import current_app
from flask.helpers import send_from_directory
from badOrderObj import badOrderObj
from flask import Flask, request, url_for, redirect, render_template
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path
from math import sqrt
import requests
import asyncio
import smtplib
import json
import time
import sys
import os

app = Flask (__name__)

config = json.load(open(Path('config.json')))
xauthtoken = config["x-auth-token"]
storehash = config["store-hash"]
configEmail = config["email"]
emailPassword = config["email-password"]

now = datetime.now()
filePath = "logs/{}.log".format(now)


def log_print(message):
    with open (filePath, 'a') as f:
        print(now, message)
        print(now, message, file=f)

#ALL ORDERS
listID = {}

#FOUND ILLEGAL ORDERS
illegal = {}
illegalObjects = {}

#illegal order canelation list
#key is orderID vaue is status_id
cancelList = {}

#! FINAL DICT
#? This dict key: ORDER_ID value: CANCELATION STATUS (possible or not possible)
result = {}

#Key: ProductID Value: List of ZipCodes
id_to_illegalZip = {}

#TODO RENAME
#LIST OF PRODUCTS AND THEIR ILLEGAL ZIPCODES
id_zip = open("id_zip.txt", "r")

for line in id_zip:
    split = line.split(":")
    id_to_illegalZip[split[0]] = split[1:]
id_zip.close()

headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'x-auth-token': xauthtoken
            }

#METHOD "INITIAL" POPULATES ALL ORDERS GIVEN A STARTING ID
#ARGS: INITIAL - IS THE STARTING ORDER ID, MUST BE A STRING!
def initial(startID):
    error = False
    num = 0

    log_print("PARSING ORDERS, STARTING FROM ORDER # " + startID)
    log_print("**************************************************************************")
    
    while error != True: #! CHANGE
        num+=1
        url = "https://api.bigcommerce.com/stores/" + str(storehash) + "/v2/orders"

        querystring = {"page":num,"min_id":startID}
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            log_print("REQUEST: Page " + str(num) + " STATUS_CODE: " + str(response.status_code))
            json_data = response.json()
        except:
            log_print("REQUEST: Page " + str(num) + " STATUS_CODE: " + str(response.status_code))
            return

        for x in json_data:
            products = []
            url = "https://api.bigcommerce.com/stores/" + str(storehash) + "/v2/orders/"+str(x['id'])+"/products"
            response = requests.request("GET", url, headers=headers)
            for j in response.json():
                products.append(j['product_id'])
            log_print("REQUEST: Indexing page " + str(num) + " adding " + str(len(products)) + " products " + str(products) + " to orderID " + str(x['id']))
            #TODO Make it so if zip has a "-" it converts it. for example "37095-9226"
            idAndZip = (str(x['id'])+":"+str(x['billing_address']['zip']))
            listID[idAndZip] = products

#CHECKS FOR ILLEGAL ZIPCODES
def checkIllegal():
    for blockedID in id_to_illegalZip:
        for orderID in listID:
            #check if the productID from [id_to_illegalZip] is in ORDER PRODUCT LISTS
            if int(blockedID) in listID[orderID]:
                #check if zipcode matches order zipcode
                splitKEY = orderID.split(":")
                orderZipcode = splitKEY[1]
                for blockedZip in id_to_illegalZip[blockedID]:
                    if orderZipcode in blockedZip:
                        key = "{}:{}".format(str(orderID),blockedID)
                        illegal[key] = listID[orderID]

async def formatResults():
    emailMessage = "****************************************************************************************************************************************************\nFOUND ORDERS WITH ITEMS THAT ARE ILLEGAL FOR THEIR ZIPCODES\n****************************************************************************************************************************************************"
    for x in result:
        emailMessage+=("*\t\nORDERID: [{}] RESULT: [{}]".format(str(x), str(result[x])))
    emailMessage+=("\n****************************************************************************************************************************************************\nDeveloped by Oze Botach - MIT LICENSE")
    return(emailMessage)

def cancelIllegalOrders():
    for order in illegal:
        split = order.split(":")
        orderID = split[0]
        url = "https://api.bigcommerce.com/stores/" + str(storehash) + "/v2/orders/"+str(orderID)

        response = requests.request("GET", url, headers=headers)
        get = response.json()
        cancelList[orderID] = get['status']

        fullName = str(get['billing_address']['first_name'])+" "+(str(get['billing_address']['last_name']))

        for canceled in cancelList:
            if response.status_code != 200:
                    log_print("ERROR WHEN TRYING TO ENACT PUT METHOD FOR ORDER CANCELING! REPORT TO OZE IF YOU SEE THIS.")
                    return

            if(get['status'] == "Awaiting Payment" or get['status'] == "Awaiting Fulfillment"):
                url2 = "https://api.bigcommerce.com/stores/" + str(storehash) + "/v2/orders/"+str(canceled)

                payload2 = "{\"status_id\":5}"

                response2 = requests.request("PUT", url2, data=payload2, headers=headers)
                    
                json_data2 = response2.json()

                currentCaneclation = badOrderObj(orderID, fullName, split[1], split[2])
                log_print("NEW OBJECT FOR CUSTOMER/ORDER: {} : {} : {} : {}".format(currentCaneclation.getOrderID(), currentCaneclation.getName(), currentCaneclation.getZipcode(), currentCaneclation.getIllegalItem()))
                key = "{}:{}".format(orderID, get['billing_address']['email'])
                illegalObjects[key] = currentCaneclation
                log_print("\nOrder [{}] was canceled!\n".format(orderID))
                result[canceled] = "Status was [{}]. Requirments fulfilled and ORDER_ID [{}] canceled! Confirmtaion: NEW_ORDER_STATUS[{}]".format(cancelList[canceled], canceled, json_data2['status'])
            else:
                url = "https://api.bigcommerce.com/stores/" + str(storehash) + "/v2/orders/"+str(canceled)

                response = requests.request("GET", url, headers=headers)
                get2 = response.json()

                cancelList[orderID] = get['status']

                result[canceled] = "Status was [{}]. Requirments FAILED to be fulfilled as ORDER_ID [{}]'s status is [{}], which means we cannot cancel!".format(cancelList[canceled], canceled, get2['status'])

            for x in result:
                log_print("Cancelation Status: {} Result: {}".format(x, result[x]))
            
# EMAIL BELOW
def emailResults(recipients):
    log_print("****************|BEGIN EMAIL SENDING|****************")
    MY_ADDRESS = configEmail
    MY_PASSWORD = emailPassword
    s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, MY_PASSWORD)

    recipients += ", oze@obotach.com"
    splitEmails = recipients.split(", ")
    for currEmail in splitEmails:
        log_print("Attempting to send email to " + currEmail)
        msg = MIMEMultipart()

        msg['From']=MY_ADDRESS
        msg['To']=currEmail
        msg['Subject']="Illegal Order Check Result"

        message=""
        logsfile = open(filePath, 'r')
        for line in logsfile:
            message+=(line)
        logsfile.close()

        msg.attach(MIMEText(message, "plain"))
        s.send_message(msg)
        log_print("Sent!")
        del msg
    log_print("****************|END OF EMAIL SENDING|****************")

# EMAIL BELOW
def emailCanceledCustomer():
    log_print("****************|BEGIN CUSTOMER ORDER CANCELATION EMAIL SENDING|****************")
    MY_ADDRESS = configEmail
    MY_PASSWORD = emailPassword
    s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, MY_PASSWORD)

    for obj in illegalObjects:
        currentSplit = obj.split(":")
        orderID = currentSplit[0]
        currEmail = currentSplit[1]
        log_print("Attempting to email {} notifying them their order has been canceled:".format(currEmail))
        msg = MIMEMultipart()

        url = "https://api.bigcommerce.com/stores/" + str(storehash) + "/v3/catalog/products/"+str(illegalObjects[obj].getIllegalItem())

        responseGETPROD = requests.request("GET", url, headers=headers)
        json_dataGETPROD = responseGETPROD.json()
        prodNAME = json_dataGETPROD['data']['name']

        msg['From']=MY_ADDRESS
        msg['To']=currEmail
        msg['Subject']="Order Number {} Canceled".format(orderID)

        message = "Hello {},\n\nYour order number '{}' has been canceled\n as it contained the item '{}' (id: {}),\n which is not purchasable in your entered zipcode '{}'.\n If you had other item(s) in your order, please re-order without the mentioned item.\n\nThank you,\nBotach Inc.".format(illegalObjects[obj].getName(), illegalObjects[obj].getOrderID(), prodNAME, illegalObjects[obj].getIllegalItem(), illegalObjects[obj].getZipcode())
        msg.attach(MIMEText(message, "plain"))
        s.send_message(msg)
        log_print("Sent!")
        del msg
    log_print("****************|END CUSTOMER ORDER CANCELATION EMAIL SENDING|****************")

async def resultUI():

    log_print("\n\n********************************************************\nResults:\n\tScanned orders: {}\n\tFound Illegal Orders: {}\n\tOrders Succesfully Cancel:{}\n********************************************************\n\nDeveloped by Oze Botach - MIT LICENSE\n".format(len(listID.keys()), len(illegal.keys()), len(illegalObjects.keys())))

    intChoice = input("Would you like to see the results here, or would you like to recieve them by email?\n\t[0] HERE IN CONSOLE\n\t[1] EMAIL\n\t[2] BOTH\n")
    choice = str(intChoice)
    if choice == "1":
        emails = input("Plese enter email(s) seperate by a SPACE and COMMA, e.x 'test@test.com, test2@test2.com':\n")
        emailResults(emails)
    elif choice == "0":
        log_print(await formatResults())
    elif choice == "2":
        emails = input("Plese enter email(s) seperate by a SPACE and COMMA, e.x 'test@test.com, test2@test2.com':\n")
        log_print(await formatResults())
        await emailResults(emails)
    
def start(id, emails):
    now = datetime.now()
    filePath = "logs/{}.log".format(now)
    try:
        os.remove("logs/latest.log")
    except:
        log_print("NO 'logs/latest.log' FOUND!")
    newFile = open(filePath, "x")
    newFile.write("Time script was ran: {}\n".format(now))
    newFile.close()
    initial(id)
    checkIllegal()
    cancelIllegalOrders()
    emailCanceledCustomer()
    emailResults(str(emails))
    #asyncio.run(resultUI())
    copyfile(filePath, "logs/latest.log")

#BEGIN FLASK
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/stream")
def stream():
    def generate():
        for i in range(500):
            yield "{}\n".format(sqrt(i))
            time.sleep(1)

    return app.response_class(generate(), mimetype="text/plain")


@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory(directory="logs/", filename="latest.log")

#background process happening without any refreshing
@app.route('/background_process', methods = ['POST', 'GET'])
def background_process():
    if request.method == 'GET':
        return render_template('restrictions.html')
    if request.method == 'POST':
        form_data = request.form
        initialOrderID = request.form.get('initialOrderID')
        emailList = request.form.get('emailList')
    start(initialOrderID, emailList)
    return render_template('restrictions.html')

@app.route('/restrictions', methods = ['POST', 'GET'])
def restrictions():
    if request.method == 'GET':
        return render_template('restrictions.html')
    # if request.method == 'POST':
    #     form_data = request.form
    #     initialOrderID = request.form.get('initialOrderID')
    #     emailList = request.form.get('emailList')

    #     return render_template('restrictions.html',form_data = form_data)

app.run(debug=True, port=5000, host='0.0.0.0')
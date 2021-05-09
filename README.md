This is an app I made for a company I work for but decided to make free.
===============	
The use case this was developed for was to restrict the orders of ammo and gun magazines by zipcode, allowing the company to not block the entire state, restricting legal zipcodes within the state from purchasing.
===============	

This project is developed in **Python**, but also uses the **Flask framework** abd **Bulma** to create a visually appealing website that manages the script/

**What does this do?**
  - Scans orders from an inputted range

  - Check if order's entered zipcode is restricted from purchasing a product within the order.

  - If the above is true, it will attempt to cancel the order and email the customer with details on why the order was canceled ONLY IF its BigCommerce status is "Awaiting Processing" or "Awaiting Payment", as this means no label or payment has been made, and thus is ok to cancel.

  - If an orders status that the program wants to cancel is NOT "Awaiting Processing" or "Awaiting Payment", it will reflect this in the output so the end user can manually hanlde this.

**How to define zipcodes that are not purchasable for a product?**
  - Open the file "**id_zip.txt**"
  - Copy the BigCommerce product id NOT the SKU. You can get the BigCommeerce product id by editing the product in the BigCommerce backend panel, and in the URL, the   ID will be the numbers before the "/edit" in the url. I.E, https://store-STORE-HASH.mybigcommerce.com/manage/products/**82782**/edit, the ID is the bolded numbers.
  - Enter the BigCommerce product ID and add a ":" after it without a space.
  - On the same line, add the zipcode(s) that are not allowed to purchase the product, seperated by ", ". I.E "82782:90035, 90036". This format is CASE-SENSITIVE
  - Seperate each product and its restructions by line.


![Preview:](https://s3.gifyu.com/images/2021-05-09-13.33.52.gif)

**How to run this app?**
- Download and in main directory add a file called "config.json"
- Copy the format for config.json below and enter the required fields
- Make a folder called logs and add an empty text file called latest.log
- Open a terminal from the folder
- Type "flask run"
- Open browser and go to "localhost:5000"

![config.json example:](https://i.ibb.co/qF0qSpV/Image-5-9-21-at-1-56-PM.jpg)

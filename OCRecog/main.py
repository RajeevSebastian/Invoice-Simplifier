import pytesseract as pt
import re
import json

text = pt.image_to_string('Sample Images/costco1.jpg')
text = ''.join([i if ord(i) < 128 else ' ' for i in text])

fs = open("text.txt", 'w')
fs.write(text)
fs.close()

# declare the variables that we will be using
discount = "0"
subtotal = "0"
totalItemsSold = "N/A"
total = "0"
tax = "0"

with open("text.txt") as fp:
    line = fp.readline().lower()
    while line:
        list = line.lower().split()
        if "subtotal" in line:
            tempSubtotal = list[-1]
            tempSubtotal = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", tempSubtotal)
            tempSubtotal = float(''.join(e for e in tempSubtotal))
            subtotal = float(subtotal)
            subtotal = tempSubtotal
        if "sub total" in line:
            tempSubtotal = list[-1]
            tempSubtotal = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", tempSubtotal)
            tempSubtotal = float(''.join(e for e in tempSubtotal))
            subtotal = float(subtotal)
            subtotal = tempSubtotal
        if "item" in line:
            totalItemsSold = list[-1]
            totalItemsSold = re.sub("[@#$%^&*(){}:‘'^A-Za-z]]", "", totalItemsSold)
        if "discount" in line:
            discount = list[-1]
            discount = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", discount)
            discount = float(''.join(e for e in discount if e.isdigit() or e == '.'))
        if "(h)hst" in line:
            tempTax = list[-1]
            tempTax = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", tempTax)
            tempTax = float(''.join(e for e in tempTax if e.isdigit() or e == '.'))
            tax = float(tax)
            tax += tempTax
        if "tax" in line:
            tempTax = list[-1]
            tempTax = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", tempTax)
            tempTax = float(''.join(e for e in tempTax if e.isdigit() or e == '.'))
            tax = float(tax)
            tax += tempTax
        if "total" in line and "subtotal" not in line and "sub total" not in line:
            tempTotal = list[-1]
            tempTotal = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", tempTotal)
            tempTotal = float(''.join(e for e in tempTotal if e.isdigit() or e == '.'))
            total = float(total)
            total += tempTotal

        line = fp.readline().lower()

subtotal = float(subtotal)
total = float(total)
discount = float(discount)
tax = float(tax)

if (total < (subtotal)):
    total = subtotal

if tax > subtotal and subtotal != 0:
    tax = 0

if tax > 0 and total <= subtotal:
    total = subtotal + tax

if subtotal == 0:
    subtotal = total - tax

resultList = {"Total items purchased": totalItemsSold, "Total before tax": subtotal,
              "Tax": round(float(tax), 2), "Total bill after tax": round(float(total), 2), "Total discount": round(float(discount), 2)}

resultList = json.dumps(resultList)
print(resultList)

#This is running fine till now
import pytesseract as pt
import re
import json
import nltk
import sys
from nltk.tag.stanford import StanfordNERTagger
from pdf2image import convert_from_path
from datetime import date
import boto3
import os

link = sys.argv[1]

filename = link.split('/')[-1]
s3 = boto3.resource('s3', aws_access_key_id=sys.argv[2],
                    aws_secret_access_key=sys.argv[3])
s3.Bucket('invoice-simplifier-file-store').download_file(filename, filename)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

if filename.split('.')[-1] == 'pdf':
    pages = convert_from_path(filename)

    for page in pages:
        page.save('out.jpg', 'JPEG')
    filename = 'out.jpg'

text = pt.image_to_string(filename)
text = ''.join([i if ord(i) < 128 else ' ' for i in text])
jar = os.path.dirname(os.path.abspath(__file__)) + '/stanford-ner.jar'
model = os.path.dirname(os.path.abspath(__file__)) +'/english.all.3class.distsim.crf.ser.gz'

# Prepare NER tagger with english model
ner_tagger = StanfordNERTagger(model, jar, encoding='utf8')

fs = open("text.txt", 'w')
fs.write(text)
fs.close()

# The below section is to get all the individual items
items = {}
if filename.split('.')[0] == 'out':
    subLine = False
    itemCount = 0
    addedItems = 0

    # Reading the file in reverse order
    for line in reversed(list(open("text.txt"))):
        if line == '\n':
            continue
        l = line.rstrip().lower().split()
        if "item" in line.lower():
            itemCount = l[-1]
            itemCount = re.sub("[@#$%^&*(){}:‘'^A-Za-z]", "0", itemCount)
            itemCount = int(itemCount.replace(',', ''))
            continue
        if subLine:
            itemName = ""
            for i in l:
                if i != l[-1]:
                    itemName += i + " "
            temp = l[-1]
            itemName = itemName.rstrip()
            temp = re.sub("[@#$%^,&*(){}:‘'^A-Za-z]", "", temp)
            temp = float(temp)
            items[itemName] = temp
            addedItems += 1
            if addedItems == itemCount:
                break
            continue
        if "subtotal" in line.lower() or "sub total" in line.lower():
            subLine = True

# declare the variables that we will be using
organization = ''
discount = "0"
subtotal = "0"
totalItemsSold = "0"
total = "0"
tax = "0"
receiptDate = "N/A"

with open("text.txt") as fp:
    line = fp.readline().lower()
    while line:
        if organization == '':
            # Tokenize: Split sentence into words
            words = nltk.word_tokenize(line)
            words = [i.upper() for i in words]
            temp = ner_tagger.tag(words)
            for i in temp:
                if i[1] == 'ORGANIZATION' or i[0] == 'WALMART' or i[0] == 'COSTCO' or i[0] == 'APNABAZAAR' or i[0] == 'AMAZON' or i[0] == 'MICROSOFT':
                    organization = i[0]
                    break
        list = line.lower().split()
        if "subtotal" in line:
            tempSubtotal = list[-1]
            tempSubtotal = re.sub("[@#$%^&,*(){}:‘'^A-Za-z]", "", tempSubtotal)
            tempSubtotal = float(''.join(e for e in tempSubtotal))
            subtotal = float(subtotal)
            subtotal = tempSubtotal
        if "sub total" in line:
            tempSubtotal = list[-1]
            tempSubtotal = re.sub("[@#$%^,&*(){}:‘'^A-Za-z]", "", tempSubtotal)
            tempSubtotal = float(''.join(e for e in tempSubtotal))
            subtotal = float(subtotal)
            subtotal = tempSubtotal
        if "item" in line:
            totalItemsSold = list[-1]
            totalItemsSold = re.sub("[@#$%^&,*(){}:‘'^A-Za-z]]", "", totalItemsSold)
            line = fp.readline().lower()
            continue
        if "discount" in line:
            discount = list[-1]
            discount = re.sub("[@#$%^&*(),{}:‘'^A-Za-z]", "", discount)
            discount = float(''.join(e for e in discount if e.isdigit() or e == '.'))
        if "(h)hst" in line:
            tempTax = list[-1]
            tempTax = re.sub("[@#$%^&*(),{}:‘'^A-Za-z]", "", tempTax)
            tempTax = float(''.join(e for e in tempTax if e.isdigit() or e == '.'))
            tax = float(tax)
            tax += tempTax
        if "tax" in line:
            tempTax = list[-1]
            tempTax = re.sub("[@#$%^&*(),{}:‘'^A-Za-z]", "", tempTax)
            tempTax = float(''.join(e for e in tempTax if e.isdigit() or e == '.'))
            tax = float(tax)
            tax += tempTax
        if "total" in line and "subtotal" not in line and "sub total" not in line:
            tempTotal = list[-1]
            tempTotal = re.sub("[@#$%^&*,(){}:‘'^A-Za-z]", "", tempTotal)
            tempTotal = float(''.join(e for e in tempTotal if e.isdigit() or e == '.'))
            total = float(total)
            total += tempTotal
        if ("receipt" in line and "date" in line) or ("invoice" in line and "date" in line):
            receiptDate = list[-1]

        line = fp.readline().lower()

subtotal = float(subtotal)
total = float(total)
discount = float(discount)
tax = float(tax)

if total < subtotal:
    total = subtotal

if tax > subtotal and subtotal != 0:
    tax = 0

if tax > 0 and total <= subtotal:
    total = subtotal + tax

if subtotal == 0:
    subtotal = total - tax

if receiptDate == "N/A":
    receiptDate = str(date.today())


resultList = {"billIssuedBy": organization, "receiptDate": receiptDate, "totalItemsPurchased": int(totalItemsSold),
              "subtotal": subtotal, "tax": round(float(tax), 2), "totalBillAfterTax": round(float(total), 2),
              "totalDiscount": round(float(discount), 2)}

lookup = {"85C Bakery Cafe": "beverage", "alterra coffee roasters": "beverage", "an giang coffee": "beverage",
          "aroma espresso bar": "beverage", "barcaffe": "beverage", "baristas": "beverage", "bewley's": "beverage",
          "black ivory coffee": "beverage", "blue bottle coffee": "beverage", "bridgehead coffee": "beverage",
          "café bom dia": "beverage", "café britt": "beverage", "café coffee day": "beverage", "cafédirect": "beverage",
          "caffè nero": "beverage", "caffé vita coffee roasting company": "beverage", "caribou coffee": "beverage",
          "coffee beanery": "beverage", "coffee island": "beverage", "coffeeshop company": "beverage",
          "colectivo coffee roaster": "beverage", "community coffee": "beverage", "coop kaffe": "beverage",
          "costa coffee": "beverage", "dallmayr": "beverage", "death wish coffee": "beverage",
          "delta cafés": "beverage", "diedrich coffee": "beverage", "douwe egberts": "beverage",
          "dulce café": "beverage", "dunkin' donuts": "beverage", "dunn bros": "beverage",
          "dutch bros. coffee": "beverage", "ellis coffee company": "beverage", "eight o'clock coffee": "beverage",
          "equal exchange": "beverage", "figaro coffee company": "beverage", "franck": "beverage",
          "gloria jean's coffees": "beverage", "highlands coffee": "beverage", "hills bros. coffee": "beverage",
          "illy": "beverage", "indian coffee house": "beverage", "jittery joe's": "beverage",
          "the j.m. smucker company": "beverage", "juan valdez café": "beverage", "julius meinl": "beverage",
          "keurig green mountain": "beverage", "koa coffee plantation": "beverage", "kraft foods": "beverage",
          "la colombe coffee roasters": "beverage", "landwer coffee": "beverage", "lavazza": "beverage",
          "massimo zanetti": "beverage", "matthew algie": "beverage", "maxwell house": "beverage",
          "meira oy": "beverage", "melitta": "beverage", "mikel coffee company": "beverage", "miko coffee": "beverage",
          "nestlé": "beverage", "new england coffee": "beverage", "paulig": "beverage", "paulig": "beverage",
          "oldtown white coffee": "beverage", "philz coffee": "beverage", "red diamond": "beverage",
          "revelator coffee": "beverage", "second cup": "beverage", "starbucks": "beverage", "strauss": "beverage",
          "tchibo": "beverage", "the coffee bean & tea leaf": "beverage", "tim hortons": "beverage",
          "top shelf coffee": "beverage", "trung nguyên": "beverage", "tully's coffee": "beverage",
          "van houtte": "beverage", "vinacafe": "beverage", "yit foh tenom coffee": "beverage",
          "abuelo": "alcohol", "admiral rodney": "alcohol", "alnwick": "alcohol", "ancient mariner": "alcohol",
          "angostura": "alcohol", "appleton": "alcohol", "arcane": "alcohol", "arechabala": "alcohol",
          "arome": "alcohol", "asta morris": "alcohol", "atlantico": "alcohol", "bacardi": "alcohol",
          "barbancourt": "alcohol", "barbieri": "alcohol", "barcelo": "alcohol", "barti ddu": "alcohol",
          "bayou": "alcohol", "bermudez": "alcohol", "berry bros & rudd": "alcohol", "bielle": "alcohol",
          "bimber": "alcohol", "black joe": "alcohol", "black magic": "alcohol", "black stripe": "alcohol",
          "black tears": "alcohol", "black tot": "alcohol", "blackmask": "alcohol", "blackwell's": "alcohol",
          "bombo": "alcohol", "bonpland": "alcohol", "botran": "alcohol", "bougainville": "alcohol",
          "bounty": "alcohol", "bristol": "alcohol", "brugal": "alcohol", "bumbu": "alcohol", "bundaberg": "alcohol",
          "burning barn": "alcohol", "butterfly": "alcohol", "by the dutch": "alcohol", "cacique": "alcohol",
          "cambridge": "alcohol", "cana brava": "alcohol", "cane island": "alcohol", "captain morgan": "alcohol",
          "cargo cult": "alcohol", "caroni": "alcohol", "cartavio": "alcohol", "cashcane": "alcohol",
          "ceylon arrack": "alcohol", "chairman's": "alcohol", "chairman's reserve": "alcohol", "chamarel": "alcohol",
          "clairin": "alcohol", "clairin vaval": "alcohol", "clarke's court": "alcohol", "clement": "alcohol",
          "cloven hoof": "alcohol", "cockspur": "alcohol", "compagnie des indes": "alcohol", "companero": "alcohol",
          "copalli": "alcohol", "cortez": "alcohol", "coruba": "alcohol", "cruzan": "alcohol", "damoiseau": "alcohol",
          "dark matter": "alcohol", "darsa": "alcohol", "dead man's fingers": "alcohol", "demerara": "alcohol",
          "depaz": "alcohol", "diablesse": "alcohol", "diamond": "alcohol", "dictador": "alcohol", "dillon": "alcohol",
          "diplomatico": "alcohol", "distillerie de paris": "alcohol", "don papa": "alcohol", "don q": "alcohol",
          "doorly's": "alcohol", "dos maderas": "alcohol", "duppy share": "alcohol", "duquesne": "alcohol",
          "east london liquor": "alcohol", "edward gunpowder": "alcohol", "el destilado": "alcohol",
          "el dorado": "alcohol", "elements eight": "alcohol", "embargo": "alcohol", "english harbour": "alcohol",
          "enmore": "alcohol", "fair": "alcohol", "fallen angel": "alcohol", "fernandes": "alcohol", "fiji": "alcohol",
          "flamboyant": "alcohol", "flor de cana": "alcohol", "forsyths": "alcohol", "foursquare": "alcohol",
          "franklin": "alcohol", "gold of mauritius": "alcohol", "gosling's": "alcohol", "green island": "alcohol",
          "guadeloupe": "alcohol", "gunroom": "alcohol", "habitation velier": "alcohol", "hampden": "alcohol",
          "hattiers": "alcohol", "havana club": "alcohol", "holey dollar": "alcohol", "hoxton": "alcohol",
          "hse": "alcohol", "iceberg": "alcohol", "inner circle": "alcohol", "isla del ron": "alcohol",
          "isla ñ": "alcohol", "izalco": "alcohol", "j bally": "alcohol", "j gow": "alcohol", "jamaica wp": "alcohol",
          "jm": "alcohol", "juan santos": "alcohol", "karukera": "alcohol", "kennedy": "alcohol",
          "kill devil": "alcohol", "koko kanu": "alcohol", "kraken": "alcohol", "la guildive": "alcohol",
          "la hechicera": "alcohol", "la mauny": "alcohol", "lamb's": "alcohol", "legendario": "alcohol",
          "liverpool": "alcohol", "long pond": "alcohol", "lost spirits": "alcohol", "lugger": "alcohol",
          "luigi bosca": "alcohol", "mamita": "alcohol", "manchester still": "alcohol", "mangoustan": "alcohol",
          "martinazzi": "alcohol", "masam": "alcohol", "matthew brown": "alcohol", "matugga": "alcohol",
          "matusalem": "alcohol", "merser": "alcohol", "mezan": "alcohol", "mhoba": "alcohol", "montero": "alcohol",
          "monymusk": "alcohol", "mount gay": "alcohol", "mount gilboa": "alcohol", "myers's": "alcohol",
          "negrillon": "alcohol", "neisson": "alcohol", "new grove": "alcohol", "nicaragua": "alcohol",
          "nine leaves": "alcohol", "ninefold": "alcohol", "nusa caña": "alcohol", "o v d": "alcohol",
          "o'hara's": "alcohol", "old j spiced": "alcohol", "old monk": "alcohol", "owney's": "alcohol",
          "pacto navio": "alcohol", "pampero": "alcohol", "panama": "alcohol", "panama red": "alcohol",
          "papagayo": "alcohol", "paranubes": "alcohol", "patalo": "alcohol", "penny blue": "alcohol",
          "pepita": "alcohol", "pere labat": "alcohol", "phoenix tears": "alcohol", "phraya": "alcohol",
          "pink pigeon": "alcohol", "pirate's grog": "alcohol", "plantation": "alcohol", "pumpkin face": "alcohol",
          "pusser's": "alcohol", "pyrat": "alcohol", "rational spirits": "alcohol", "real mccoy": "alcohol",
          "rebellion": "alcohol", "red bonny": "alcohol", "red heart": "alcohol", "red leg": "alcohol",
          "relicario": "alcohol", "rhum du matelot": "alcohol", "rhum rhum": "alcohol", "rhum superieur": "alcohol",
          "rock star": "alcohol", "ron abuelo": "alcohol", "ron aguere": "alcohol", "ron centenario": "alcohol",
          "ron cubay": "alcohol", "ron de jeremy": "alcohol", "ron esclavo": "alcohol", "ron zacapa": "alcohol",
          "rumbar": "alcohol", "rumjava": "alcohol", "rumshak": "alcohol", "ryoma": "alcohol",
          "sailor jerry": "alcohol", "saint james": "alcohol", "salford": "alcohol", "samaroli": "alcohol",
          "sangsom": "alcohol", "santa lucilia": "alcohol", "santa teresa": "alcohol", "santiago de cuba": "alcohol",
          "savanna": "alcohol", "scratch": "alcohol", "seawolf": "alcohol", "seven fathoms": "alcohol",
          "single barrel selection": "alcohol", "sixty six": "alcohol", "skipper": "alcohol", "smatt's": "alcohol",
          "smith & cross": "alcohol", "sparrow's": "alcohol", "spytail": "alcohol", "st aubin": "alcohol",
          "st james": "alcohol", "st lucia": "alcohol", "st nicholas": "alcohol", "st nicholas abbey": "alcohol",
          "stock": "alcohol", "stork club": "alcohol", "stroh": "alcohol", "sunset": "alcohol", "sweetdram": "alcohol",
          "takamaka": "alcohol", "thameside": "alcohol", "that boutique-y rum company": "alcohol",
          "the real mccoy": "alcohol", "tiki lovers": "alcohol", "tilambic": "alcohol", "toti": "alcohol",
          "toti rum": "alcohol", "travellers": "alcohol", "trinidad": "alcohol",
          "trinidad distillers limited": "alcohol", "trois rivieres": "alcohol", "two swallows": "alcohol",
          "uitvlugt": "alcohol", "union": "alcohol", "valdespino": "alcohol", "vale royal": "alcohol",
          "various": "alcohol", "velier": "alcohol", "veritas": "alcohol", "vigia": "alcohol",
          "virgin gorda": "alcohol", "watson's": "alcohol", "west indies": "alcohol", "westerhall estate": "alcohol",
          "wild tiger": "alcohol", "william george": "alcohol", "wood's": "alcohol", "world's end": "alcohol",
          "worthy park": "alcohol", "wray & nephew": "alcohol", "xm": "alcohol", "zafra": "alcohol", "zaya": "alcohol",
          "zuidam": "alcohol", "absolut": "alcohol", "adnams": "alcohol", "aivy": "alcohol", "alchemia": "alcohol",
          "arbikie": "alcohol", "au": "alcohol", "audemus": "alcohol", "aylesbury duck": "alcohol",
          "babicka": "alcohol", "baczewski": "alcohol", "ballast point": "alcohol", "baller": "alcohol",
          "belenkaya": "alcohol", "beluga": "alcohol", "belvedere": "alcohol", "bimber": "alcohol",
          "black cow": "alcohol", "blackdown": "alcohol", "blackwoods": "alcohol", "blavod": "alcohol",
          "bloodshot": "alcohol", "boatyard": "alcohol", "boston": "alcohol", "brecon": "alcohol",
          "brennen & brown": "alcohol", "brochan": "alcohol", "broken clock": "alcohol", "bullet": "alcohol",
          "cariel": "alcohol", "charbay": "alcohol", "chase": "alcohol", "chilgrove": "alcohol", "chopin": "alcohol",
          "ciroc": "alcohol", "cold river": "alcohol", "copernicus": "alcohol", "corsair": "alcohol",
          "cossack": "alcohol", "cracovia": "alcohol", "crystal head": "alcohol", "curio": "alcohol",
          "davna": "alcohol", "death's door": "alcohol", "debowa polska": "alcohol", "dingle": "alcohol",
          "distillerie de paris": "alcohol", "east london liquor": "alcohol", "eesti": "alcohol", "effen": "alcohol",
          "eight lands": "alcohol", "element 29": "alcohol", "eristoff": "alcohol", "fair": "alcohol",
          "fallen angel": "alcohol", "figenza": "alcohol", "finlandia": "alcohol", "firefly": "alcohol",
          "firestarter": "alcohol", "general john stark": "alcohol", "ghost": "alcohol", "gold wasser": "alcohol",
          "grand touring": "alcohol", "grasovka": "alcohol", "green mark": "alcohol", "grey goose": "alcohol",
          "heartland": "alcohol", "hepple douglas": "alcohol", "holy grass": "alcohol", "iceberg": "alcohol",
          "icelandic mountain": "alcohol", "impuls": "alcohol", "iordanov": "alcohol", "isfjord": "alcohol",
          "ivan the terrible": "alcohol", "jelley's": "alcohol", "jewel of russia": "alcohol", "jj whitley": "alcohol",
          "kakuzo": "alcohol", "kalak": "alcohol", "kalevala": "alcohol", "karven": "alcohol", "kauffman": "alcohol",
          "kavka": "alcohol", "ketel one": "alcohol", "konik's tail": "alcohol", "koskenkorva": "alcohol",
          "krupnik": "alcohol", "kubanskaya": "alcohol", "kuzmich": "alcohol", "lanique": "alcohol",
          "legend of kremlin": "alcohol", "liverpool": "alcohol", "long table": "alcohol", "luksusowa": "alcohol",
          "mamont": "alcohol", "manly spirits": "alcohol", "mikkeller": "alcohol", "moskovskaya": "alcohol",
          "motörhead": "alcohol", "nemiroff": "alcohol", "nikka": "alcohol", "oddka": "alcohol",
          "okhotnichya": "alcohol", "our london": "alcohol", "pienaar and son": "alcohol", "pincer": "alcohol",
          "polmos": "alcohol", "polugar": "alcohol", "prairie": "alcohol", "pravda": "alcohol", "precious": "alcohol",
          "pure": "alcohol", "ramsbury": "alcohol", "red eye louie's": "alcohol", "reyka": "alcohol",
          "rigas": "alcohol", "roberto cavalli": "alcohol", "rock sea": "alcohol", "rogue": "alcohol",
          "russian standard": "alcohol", "russkaya": "alcohol", "rutte": "alcohol", "sacred": "alcohol",
          "sapling": "alcohol", "sausage tree": "alcohol", "sauvelle": "alcohol", "sipsmith": "alcohol",
          "siwucha": "alcohol", "skyy": "alcohol", "smirnoff": "alcohol", "smith & sinclair": "alcohol",
          "snow": "alcohol", "snow queen": "alcohol", "spirit of hven": "alcohol", "sputnik": "alcohol",
          "square one": "alcohol", "st george": "alcohol", "staritsky levitsky": "alcohol", "stolichnaya": "alcohol",
          "stolowa": "alcohol", "tanqueray": "alcohol", "the lakes": "alcohol", "three olives": "alcohol",
          "tito's": "alcohol", "todka": "alcohol", "uk5": "alcohol", "ultimat": "alcohol", "uluvka": "alcohol",
          "underground": "alcohol", "ursus": "alcohol", "v gallery": "alcohol", "various": "alcohol", "vela": "alcohol",
          "ver2": "alcohol", "viche pitia": "alcohol", "victory": "alcohol", "virtuous": "alcohol", "vka": "alcohol",
          "whitley neill": "alcohol", "wry": "alcohol", "wyborowa": "alcohol", "xero": "alcohol",
          "zlota jesien": "alcohol", "zoladkowa": "alcohol", "zubrovka": "alcohol", "zubrowka": "alcohol",
          "ac-dc ac-dc": "alcohol", "alebrijesalebrijes": "alcohol", "ambhar ambhar": "alcohol",
          "apocalypto apocalypto": "alcohol", "aquarivaaquariva": "alcohol", "arettearette": "alcohol",
          "avion avion": "alcohol", "berrueco rockberrueco rock": "alcohol", "cabo wabocabo wabo": "alcohol",
          "calle 23calle 23": "alcohol", "cantinerocantinero": "alcohol", "casa noblecasa noble": "alcohol",
          "casamigoscasamigos": "alcohol", "casco viejo casco viejo": "alcohol", "casino azulcasino azul": "alcohol",
          "cazcabelcazcabel": "alcohol", "cenote cenote": "alcohol", "chaquirachaquira": "alcohol",
          "chayachaya": "alcohol", "chimayo chimayo": "alcohol", "clase azulclase azul": "alcohol",
          "coa de jima coa de jima": "alcohol", "codigo 1530codigo 1530": "alcohol", "corazoncorazon": "alcohol",
          "corralejocorralejo": "alcohol", "curadocurado": "alcohol", "don agustindon agustin": "alcohol",
          "don alvaro don alvaro": "alcohol", "don angeldon angel": "alcohol", "don fulanodon fulano": "alcohol",
          "don juliodon julio": "alcohol", "dona celiadona celia": "alcohol", "dos artesdos artes": "alcohol",
          "el conde azulel conde azul": "alcohol", "el jimadorel jimador": "alcohol", "el mayorel mayor": "alcohol",
          "el rayo el rayo": "alcohol", "el tesoroel tesoro": "alcohol", "enemigoenemigo": "alcohol",
          "espolonespolon": "alcohol", "fortalezafortaleza": "alcohol", "g4 g4": "alcohol",
          "gran centenariogran centenario": "alcohol", "gran corralejogran corralejo": "alcohol",
          "gran orendaingran orendain": "alcohol", "herencia de plataherencia de plata": "alcohol",
          "herraduraherradura": "alcohol", "jose cuervojose cuervo": "alcohol",
          "joyas de mexicojoyas de mexico": "alcohol", "kahkah": "alcohol", "karma karma": "alcohol",
          "la certezala certeza": "alcohol", "la puerta negrala puerta negra": "alcohol",
          "legenda del milagrolegenda del milagro": "alcohol", "lunazul lunazul": "alcohol",
          "maestromaestro": "alcohol", "maestro dobelmaestro dobel": "alcohol", "maracamemaracame": "alcohol",
          "milagromilagro": "alcohol", "ochoocho": "alcohol", "olmecaolmeca": "alcohol", "pasote pasote": "alcohol",
          "patronpatron": "alcohol", "peligrosopeligroso": "alcohol", "porfidioporfidio": "alcohol",
          "pura vida pura vida": "alcohol", "red eye louie'sred eye louie's": "alcohol",
          "reserva del senorreserva del senor": "alcohol", "satrynasatryna": "alcohol", "sauzasauza": "alcohol",
          "señor artesanoseñor artesano": "alcohol", "t1 t1": "alcohol", "tapatiotapatio": "alcohol",
          "tequila 1519 tequila 1519": "alcohol", "terralta terralta": "alcohol", "uwauwa": "alcohol",
          "villa lobosvilla lobos": "alcohol", "viviana viviana": "alcohol", "vivir vivir": "alcohol",
          "a&e": "electronics", "a.saks": "electronics", "abc": "electronics", "acer": "electronics",
          "adesso": "electronics", "aduro": "electronics", "aftershokz": "electronics",
          "aimee kestenberg": "electronics", "alcatel": "electronics", "alesis": "electronics", "ally": "electronics",
          "aluratek": "electronics", "amazon": "software", "amc": "electronics", "amped wireless": "electronics",
          "antennas direct": "electronics", "antop": "electronics", "ape case": "electronics", "apple": "electronics",
          "arcade1up": "electronics", "arlo": "electronics", "astro gaming": "electronics", "asus": "electronics",
          "at&t": "electronics", "atari": "electronics", "atomxs": "electronics", "audio-technica": "electronics",
          "august": "electronics", "autel robotics": "electronics", "avanti": "electronics", "axess": "electronics",
          "axis": "electronics", "azio": "electronics", "badash": "electronics", "baggallini": "electronics",
          "beats by dr. dre": "electronics", "befree sound": "electronics", "belkin": "electronics",
          "ben sherman": "electronics", "bionik": "electronics", "black & decker": "electronics",
          "blink": "electronics", "blue microphones": "electronics", "blueparrott": "electronics",
          "body glove": "electronics", "bose": "electronics", "bower": "electronics", "bracketron": "electronics",
          "braven": "electronics", "breville": "electronics", "brydge": "electronics",
          "buena vista home video": "electronics", "bushnell": "electronics", "call control": "electronics",
          "canon": "electronics", "capturing couture": "electronics", "case logic": "electronics",
          "casemate": "electronics", "caso design": "electronics", "caterpillar": "electronics",
          "cavalier": "electronics", "celestron": "electronics", "chamberlain": "electronics",
          "chargehub": "electronics", "cinemood": "electronics", "clamp champion": "electronics",
          "cobaltx": "electronics", "cobra": "electronics", "cocoon innovations": "electronics",
          "codemasters": "electronics", "coleman": "electronics", "coolgrips": "electronics",
          "copa judaica": "electronics", "corsair": "electronics", "cpr call blocker": "electronics",
          "cropper hopper": "electronics", "crosley": "electronics", "cta digital": "electronics",
          "cuisinart": "electronics", "danby": "electronics", "darice": "electronics", "datalogixx": "electronics",
          "dayspring": "electronics", "dell": "electronics", "dietmaster": "electronics", "digiland": "electronics",
          "digipower": "electronics", "digital gadgets": "electronics", "directv": "electronics",
          "disney": "electronics", "divoom": "electronics", "dji": "electronics", "doodlebug": "electronics",
          "ea sports": "electronics", "eco style": "electronics", "educational insights": "electronics",
          "eero": "electronics", "electro boss": "electronics", "elite screens": "electronics",
          "elizabeth taylor": "electronics", "ematic": "electronics", "embracecase": "electronics",
          "emerson": "electronics", "endust": "electronics", "energizer": "electronics", "enhance": "electronics",
          "erin condren": "electronics", "escort": "electronics", "ezviz": "electronics", "facebook": "electronics",
          "farberware": "electronics", "fellowes": "electronics", "fitbit": "electronics", "flipy": "electronics",
          "fox": "electronics", "fox & summit": "electronics", "fox luggage": "electronics",
          "frigidaire": "electronics", "fuji": "electronics", "ful": "electronics", "garmin": "electronics",
          "gear beast": "electronics", "general electric": "electronics", "globe electric": "electronics",
          "gogroove": "electronics", "google": "electronics", "gopro": "electronics", "gpx": "electronics",
          "guard your id": "electronics", "guardzilla": "electronics", "haier": "electronics",
          "hallmark": "electronics", "halo": "electronics", "harman/kardon": "electronics", "hauppauge": "electronics",
          "hbo": "electronics", "hedgren": "electronics", "hello kitty": "electronics", "hera": "electronics",
          "heritage luggage": "electronics", "hideit": "electronics", "hitachi": "electronics",
          "homedics": "electronics", "honey-can-do": "electronics", "honeywell": "electronics", "honora": "electronics",
          "hover-way": "electronics", "hp": "electronics", "hypergear": "electronics", "i'm game": "electronics",
          "icozy": "electronics", "idevices": "electronics", "ifrogz": "electronics", "igloo": "electronics",
          "ihome": "electronics", "ikeyp": "electronics", "ilive": "electronics", "iluv": "electronics",
          "image entertainment": "electronics", "imco watch": "electronics", "impecca": "electronics",
          "incase": "electronics", "innovative technology": "electronics", "iolo": "electronics", "ion": "electronics",
          "iring": "electronics", "iris": "electronics", "irobot": "electronics", "isound": "electronics",
          "iview": "electronics", "iwalk": "electronics", "jabra": "electronics", "jam wireless audio": "electronics",
          "jbl": "electronics", "jean paul usa": "electronics", "jeeo": "electronics", "jensen": "electronics",
          "jumpsmart": "electronics", "juuk": "electronics", "jvc": "electronics", "kalorik": "electronics",
          "kanex": "electronics", "kangaroo": "electronics", "karla hanson": "electronics", "keysmart": "electronics",
          "kitsound": "electronics", "klipsch": "electronics", "kng america": "electronics", "knz": "electronics",
          "koch records": "electronics", "kodak": "electronics", "koss": "electronics", "la crosse": "electronics",
          "laplink": "electronics", "laud": "electronics", "lax gadgets": "electronics", "le donne": "electronics",
          "learning resources": "electronics", "lee sands": "electronics", "legacybox": "electronics",
          "leica": "electronics", "lenovo": "electronics", "lg electronics": "electronics", "libratone": "electronics",
          "lifestyle advanced": "electronics", "link2home": "electronics", "linksys": "electronics",
          "linsay": "electronics", "lionsgate": "electronics", "litmor": "electronics", "lodis": "electronics",
          "logitech": "electronics", "lori greiner": "electronics", "lovehandle": "electronics",
          "macally": "electronics", "magic chef": "electronics", "magnavox": "electronics",
          "matr boomie": "electronics", "megamounts": "electronics", "memorex": "electronics",
          "microsoft": "software", "midland": "electronics", "mightyskins": "electronics",
          "mill creek entertainment": "electronics", "milo": "electronics", "mindscope": "electronics",
          "minolta": "electronics", "mlb": "electronics", "mobilespec": "electronics", "moft": "electronics",
          "mohu": "electronics", "momentum": "electronics", "monster cable": "electronics", "monument": "electronics",
          "mophie": "electronics", "motorola": "electronics", "msi": "electronics", "mustang av": "electronics",
          "my arcade": "electronics", "my audio pet": "electronics", "nascar": "electronics",
          "national geographic": "electronics", "naxa": "electronics", "naztech": "electronics",
          "neato robotics": "electronics", "nest": "electronics", "netgear": "electronics", "newair": "electronics",
          "nfl": "electronics", "nickelodeon": "electronics", "nikon": "electronics", "nintendo": "electronics",
          "novi": "electronics", "nyko": "electronics", "oaxis": "electronics", "olympus": "electronics",
          "omnicharge": "electronics", "omnimount": "electronics", "one for all": "electronics",
          "optoma": "electronics", "packard bell": "electronics", "panasonic": "electronics",
          "paramount pictures": "electronics", "paww": "electronics", "pbs": "electronics",
          "peace love world": "electronics", "peanuts": "electronics", "peerless": "electronics",
          "peugeot": "electronics", "philips": "electronics", "pictar": "electronics", "picture keeper": "electronics",
          "pilot": "electronics", "pioneer": "electronics", "plantronics": "electronics", "polaroid": "electronics",
          "polk": "electronics", "promounts": "electronics", "proscan": "electronics", "pyle": "electronics",
          "q-see": "electronics", "qfx": "electronics", "quicken": "electronics", "rand mcnally": "electronics",
          "rca": "electronics", "remo": "electronics", "reprize": "electronics", "resqstick": "electronics",
          "revolve": "electronics", "ring": "electronics", "riptunes": "electronics", "roadking": "electronics",
          "roku": "electronics", "royal": "electronics", "royce leather": "electronics", "rush charge": "electronics",
          "sakar": "electronics", "samsung": "electronics", "sandisk": "electronics", "sandy lisa": "electronics",
          "scosche": "electronics", "sega": "electronics", "sengled": "electronics", "sennheiser": "electronics",
          "sensi": "electronics", "shark proof": "electronics", "sharp": "electronics", "sharper image": "electronics",
          "sharpie": "electronics", "showtime entertainment": "electronics", "sima": "electronics",
          "simplisafe": "electronics", "singing machine": "electronics", "skech": "electronics",
          "skullcandy": "electronics", "skyrider": "electronics", "sol republic": "electronics",
          "solaire": "electronics", "sonos": "electronics", "sony": "electronics", "soundstream": "electronics",
          "spectra": "electronics", "sprigs": "electronics", "spt": "electronics", "square enix": "electronics",
          "squaretrade": "electronics", "star wars": "electronics", "sublue": "electronics",
          "supersonic": "electronics", "surebonder": "electronics", "surecall": "electronics",
          "surfeasy": "electronics", "suze orman": "electronics", "switchmate": "electronics",
          "sylvania": "electronics", "tapplock": "electronics", "tcl": "electronics", "team marketing": "electronics",
          "techni mobili": "electronics", "techni sport": "electronics", "tf publishing": "electronics",
          "the sak": "electronics", "thomson": "electronics", "thrustmaster": "electronics", "tikitunes": "electronics",
          "tile": "electronics", "tokk": "electronics", "torro": "electronics", "toshiba": "electronics",
          "toucan": "electronics", "tp-link": "electronics", "travelon": "electronics", "trend micro": "electronics",
          "trexonic": "electronics", "tripp lite": "electronics", "twelve south": "electronics",
          "twentieth century fox": "electronics", "two's company": "electronics", "tylt": "electronics",
          "u brands": "electronics", "ultimate ears": "electronics",
          "ultimate innovations by the depalmas": "electronics", "uniden": "electronics",
          "universal studios": "electronics", "us army": "electronics", "vera bradley": "electronics",
          "verbatim": "electronics", "victrola": "electronics", "vidbox": "electronics", "villacera": "electronics",
          "vipre": "electronics", "visual land": "electronics", "vizio": "electronics", "voguestrap": "electronics",
          "volkano": "electronics", "vtech": "electronics", "vupoint solutions": "electronics",
          "warner bros.": "electronics", "wasserstein": "electronics", "weatherx": "electronics",
          "webroot": "electronics", "westinghouse": "electronics", "whistler": "electronics",
          "whitestar": "electronics", "whoosh!": "electronics", "wicked audio": "electronics",
          "wincleaner": "electronics", "winegard": "electronics", "woodcessories": "electronics",
          "wraps": "electronics", "wyze": "electronics", "x-mini": "electronics", "yamaha": "electronics",
          "zagg": "electronics", "zeki": "electronics", "zenmate": "electronics", "zerotech": "electronics",
          "zvox": "electronics", "zyxel": "electronics", "360 electrical": "electronics", "3plus": "electronics",
          "cactuspear": "fruit", "cherimoya": "fruit", "clementines": "fruit", "dates": "fruit", "grapefruit": "fruit",
          "kiwifruit": "fruit", "orange": "fruit", "passionfruit": "fruit", "pear": "fruit", "persimmons": "fruit",
          "pummelo": "fruit", "redbanana": "fruit", "redcurrants": "fruit", "sharonfruit": "fruit",
          "tangerines": "fruit", "apples": "fruit", "apricots": "fruit", "avocados": "fruit", "bananas": "fruit",
          "cranberries": "fruit", "coconut": "fruit", "kiwano": "fruit", "lemons": "fruit", "papayas": "fruit",
          "apricots": "fruit", "barbadoscherries": "fruit", "bittermelon": "fruit", "cherimoya": "fruit",
          "honeydew": "fruit", "jackfruit": "fruit", "limes": "fruit", "lychee": "fruit", "mango": "fruit",
          "oranges": "fruit", "pineapple": "fruit", "strawberries": "fruit", "apricots": "fruit", "asianpear": "fruit",
          "barbadoscherries": "fruit", "blackcurrants": "fruit", "blackberries": "fruit", "blueberries": "fruit",
          "boysenberries": "fruit", "breadfruit": "fruit", "cantaloupe": "fruit", "casabamelon": "fruit",
          "champagnegrapes": "fruit", "cherries": "fruit", "cherries": "fruit", "sour": "fruit",
          "crenshawmelon": "fruit", "durian": "fruit", "elderberries": "fruit", "figs": "fruit", "grapefruit": "fruit",
          "grapes": "fruit", "honeydewmelons": "fruit", "jackfruit": "fruit", "keylimes": "fruit", "limes": "fruit",
          "loganberries": "fruit", "longan": "fruit", "loquat": "fruit", "lychee": "fruit", "mulberries": "fruit",
          "nectarines": "fruit", "olallieberries": "fruit", "passionfruit": "fruit", "peaches": "fruit",
          "persianmelon": "fruit", "plums": "fruit", "raspberries": "fruit", "sapodillas": "fruit", "sapote": "fruit",
          "strawberries": "fruit", "sugarapple": "fruit", "watermelon": "fruit", "asianpear": "fruit",
          "barbadoscherries": "fruit", "cactuspear": "fruit", "capegooseberries": "fruit", "crabapples": "fruit",
          "cranberries": "fruit", "feijoa": "fruit", "grapes": "fruit", "guava": "fruit", "huckleberries": "fruit",
          "jujube": "fruit", "keylimes": "fruit", "kumquats": "fruit", "muscadinegrapes": "fruit", "mushrooms": "fruit",
          "passionfruit": "fruit", "pear": "fruit", "persimmons": "fruit", "pineapple": "fruit", "pomegranate": "fruit",
          "quince": "fruit", "sapote": "fruit", "sharonfruit": "fruit", "sugarapple": "fruit",
          "5.11 tactical": "clothing", "7 for all mankind": "clothing", "'47 (brand)": "clothing",
          "6126 (clothing line)": "clothing", "a.k.o.o. clothing": "clothing", "abby z.": "clothing",
          "abercrombie & fitch": "clothing", "5.11 tactical ": "clothing", "7 for all mankind": "clothing",
          "47 (brand)": "clothing", "6126 (clothing line)": "clothing", "a.k.o.o. clothing": "clothing",
          "abby z.": "clothing", "abercrombie & fitch": "clothing", "acapulco gold (clothing brand)": "clothing",
          "acorn stores": "clothing", "aeropostale": "clothing", "agv sports group": "clothing",
          "al wissam": "clothing", "american apparel": "clothing", "american eagle outfitters": "clothing",
          "anarchic adjustment": "clothing", "anchor blue clothing company": "clothing", "andrew christian": "clothing",
          "andrew marc": "clothing", "angels jeanswear": "clothing", "anthropologie": "clothing",
          "anti social social club": "clothing", "apple bottoms": "clothing", "aquashift": "clothing",
          "ashworth (clothing)": "clothing", "atticus clothing": "clothing", "avirex": "clothing",
          "baby gap": "clothing", "baby phat": "clothing", "baci lingerie": "clothing", "banana republic": "clothing",
          "ben davis (clothing)": "clothing", "bernini (fashion)": "clothing", "bhldn": "clothing",
          "big johnson": "clothing", "bill blass group": "clothing",
          "billionaire boys club (clothing retailer)": "clothing", "blair corporation": "clothing",
          "bobby jack brand": "clothing", "born uniqorn": "clothing", "botany 500": "clothing",
          "brooks brothers": "clothing", "thom browne": "clothing", "buck mason": "clothing",
          "buckle (clothing retailer)": "clothing", "callaway golf company": "clothing",
          "calvin klein (company)": "clothing", "carlos campos (clothing brand)": "clothing", "capezio": "clothing",
          "carhartt": "clothing", "carlisle collection": "clothing", "justin cassin": "clothing",
          "charivari (store)": "clothing", "charlotte russe (clothing retailer)": "clothing",
          "charming charlie": "clothing", "cherokee inc.": "clothing", "chrome hearts": "clothing",
          "ck calvin klein": "clothing", "club monaco": "clothing", "coach new york": "clothing",
          "coldwater creek": "clothing", "columbia sportswear": "clothing", "commonwealth utilities": "clothing",
          "converse (shoe company)": "clothing", "crazy shirts": "clothing", "cross colours": "clothing",
          "dana buchman": "clothing", "dcma collective": "clothing", "delia's": "clothing",
          "discovery expedition (clothing)": "clothing", "dkny": "clothing", "dl1961": "clothing",
          "dockers (brand)": "clothing", "dollie & me": "clothing", "dolls kill": "clothing",
          "draper james": "clothing", "duck head": "clothing", "e. y. wada": "clothing", "eckhaus latta": "clothing",
          "ecko unltd.": "clothing", "eddie bauer": "clothing", "edun live on campus": "clothing",
          "eggie (brand)": "clothing", "the elder statesman (brand)": "clothing", "element skateboards": "clothing",
          "elizabeth suzann": "clothing", "ella moss": "clothing", "emel fashion": "clothing",
          "enfants riches déprimés": "clothing", "equipment (clothing brand)": "clothing",
          "etcetera (clothing brand)": "clothing", "etnies": "clothing", "ex-boyfriend": "clothing",
          "fabletics": "clothing", "famous stars and straps": "clothing", "femme for dkny": "clothing",
          "figs ties": "clothing", "filson (company)": "clothing", "the fly stop": "clothing", "forever 21": "clothing",
          "fossil group": "clothing", "free people": "clothing", "freshjive": "clothing", "frostline kits": "clothing",
          "fubu": "clothing", "fuchsia (clothing)": "clothing", "fuct (clothing)": "clothing",
          "diane von fürstenberg": "clothing", "g-unit clothing company": "clothing", "gant (retailer)": "clothing",
          "gap inc.": "clothing", "gap kids": "clothing", "georgine": "clothing", "gilly hicks": "clothing",
          "gitman bros": "clothing", "golf wang": "clothing", "guess (clothing)": "clothing", "gypsy sport": "clothing",
          "hamilton shirts": "clothing", "c.f. hathaway company": "clothing", "haus alkire": "clothing",
          "healthtex": "clothing", "helm boots": "clothing", "tommy hilfiger (company)": "clothing",
          "hollister co.": "clothing", "house of deréon": "clothing", "the hundreds": "clothing",
          "i. spiewak & sons": "clothing", "ike behar": "clothing", "imitation of christ (designs)": "clothing",
          "inamorata (brand)": "clothing", "isko (clothing company)": "clothing", "island company": "clothing",
          "ivy park": "clothing", "izod": "clothing", "j. press": "clothing", "j.crew": "clothing",
          "jams (clothing line)": "clothing", "jennifer lopez collection": "clothing",
          "the jessica simpson collection": "clothing", "j.lo by jennifer lopez": "clothing", "jnco": "clothing",
          "john varvatos (company)": "clothing", "johnny cupcakes": "clothing", "johnston & murphy": "clothing",
          "jordache": "clothing", "jovani fashion": "clothing", "jovovich-hawk": "clothing",
          "juicy couture": "clothing", "karen kane": "clothing", "kani ladies": "clothing", "karmaloop": "clothing",
          "kate spade & company": "clothing", "kenneth cole productions": "clothing",
          "alan king (designer)": "clothing", "kühl (clothing)": "clothing", "l.a.m.b.": "clothing",
          "l.e.i.": "clothing", "l.l.bean": "clothing", "l.l.bean signature": "clothing",
          "la denim atelier": "clothing", "lands' end": "clothing", "le tigre (clothing brand)": "clothing",
          "lee (jeans)": "clothing", "level 27 clothing": "clothing", "levi strauss & co.": "clothing",
          "lids (store)": "clothing", "lifted research group": "clothing", "lilli ann": "clothing",
          "live breathe futbol": "clothing", "loden dager": "clothing", "los angeles apparel": "clothing",
          "lucky brand jeans": "clothing", "lularoe": "clothing", "macbeth footwear": "clothing",
          "mainbocher": "clothing", "marc anthony collection": "clothing", "marchesa (brand)": "clothing",
          "martin + osa": "clothing", "sid mashburn": "clothing", "massive goods": "clothing", "mataano": "clothing",
          "members only (fashion brand)": "clothing", "metal mulisha": "clothing", "milly (fashion brand)": "clothing",
          "ministry of supply (clothing)": "clothing", "mitchell & ness": "clothing", "mossimo": "clothing",
          "munsingwear": "clothing", "nice collective": "clothing", "no fear": "clothing", "noah (brand)": "clothing",
          "the north face": "clothing", "number lab": "clothing", "oaklandish": "clothing", "ocean pacific": "clothing",
          "old navy": "clothing", "opening ceremony (brand)": "clothing", "original penguin": "clothing",
          "orvis": "clothing", "oshkosh b'gosh": "clothing", "acapulco gold (clothing brand)": "clothing",
          "acorn stores": "clothing", "aeropostale": "clothing", "agv sports group": "clothing",
          "al wissam": "clothing", "american apparel": "clothing", "american eagle outfitters": "clothing",
          "anarchic adjustment": "clothing", "anchor blue clothing company": "clothing", "andrew christian": "clothing",
          "andrew marc": "clothing", "angels jeanswear": "clothing", "anthropologie": "clothing",
          "anti social social club": "clothing", "apple bottoms": "clothing", "aquashift": "clothing",
          "ashworth (clothing)": "clothing", "atticus clothing": "clothing", "avirex": "clothing",
          "baby gap": "clothing", "baby phat": "clothing", "baci lingerie": "clothing", "banana republic": "clothing",
          "ben davis (clothing)": "clothing", "bernini (fashion)": "clothing", "bhldn": "clothing",
          "big johnson": "clothing", "bill blass group": "clothing",
          "billionaire boys club (clothing retailer)": "clothing", "blair corporation": "clothing",
          "bobby jack brand": "clothing", "born uniqorn": "clothing", "botany 500": "clothing",
          "brooks brothers": "clothing", "thom browne": "clothing", "buck mason": "clothing",
          "buckle (clothing retailer)": "clothing", "callaway golf company": "clothing",
          "calvin klein (company)": "clothing", "carlos campos (clothing brand)": "clothing", "capezio": "clothing",
          "carhartt": "clothing", "carlisle collection": "clothing", "justin cassin": "clothing",
          "charivari (store)": "clothing", "charlotte russe (clothing retailer)": "clothing",
          "charming charlie": "clothing", "cherokee inc.": "clothing", "chrome hearts": "clothing",
          "ck calvin klein": "clothing", "club monaco": "clothing", "coach new york": "clothing",
          "coldwater creek": "clothing", "columbia sportswear": "clothing", "commonwealth utilities": "clothing",
          "converse (shoe company)": "clothing", "crazy shirts": "clothing", "cross colours": "clothing",
          "dana buchman": "clothing", "dcma collective": "clothing", "delia's": "clothing",
          "discovery expedition (clothing)": "clothing", "dkny": "clothing", "dl1961": "clothing",
          "dockers (brand)": "clothing", "dollie & me": "clothing", "dolls kill": "clothing",
          "draper james": "clothing", "duck head": "clothing", "e. y. wada": "clothing", "eckhaus latta": "clothing",
          "ecko unltd.": "clothing", "eddie bauer": "clothing", "edun live on campus": "clothing",
          "eggie (brand)": "clothing", "the elder statesman (brand)": "clothing", "element skateboards": "clothing",
          "elizabeth suzann": "clothing", "ella moss": "clothing", "emel fashion": "clothing",
          "enfants riches déprimés": "clothing", "equipment (clothing brand)": "clothing",
          "etcetera (clothing brand)": "clothing", "etnies": "clothing", "ex-boyfriend": "clothing",
          "fabletics": "clothing", "famous stars and straps": "clothing", "femme for dkny": "clothing",
          "figs ties": "clothing", "filson (company)": "clothing", "the fly stop": "clothing", "forever 21": "clothing",
          "fossil group": "clothing", "free people": "clothing", "freshjive": "clothing", "frostline kits": "clothing",
          "fubu": "clothing", "fuchsia (clothing)": "clothing", "fuct (clothing)": "clothing",
          "diane von fürstenberg": "clothing", "g-unit clothing company": "clothing", "gant (retailer)": "clothing",
          "gap inc.": "clothing", "gap kids": "clothing", "georgine": "clothing", "gilly hicks": "clothing",
          "gitman bros": "clothing", "golf wang": "clothing", "guess (clothing)": "clothing", "gypsy sport": "clothing",
          "hamilton shirts": "clothing", "c.f. hathaway company": "clothing", "haus alkire": "clothing",
          "healthtex": "clothing", "helm boots": "clothing", "tommy hilfiger (company)": "clothing",
          "hollister co.": "clothing", "house of deréon": "clothing", "the hundreds": "clothing",
          "i. spiewak & sons": "clothing", "ike behar": "clothing", "imitation of christ (designs)": "clothing",
          "inamorata (brand)": "clothing", "isko (clothing company)": "clothing", "island company": "clothing",
          "ivy park": "clothing", "izod": "clothing", "j. press": "clothing", "j.crew": "clothing",
          "jams (clothing line)": "clothing", "jennifer lopez collection": "clothing",
          "the jessica simpson collection": "clothing", "j.lo by jennifer lopez": "clothing", "jnco": "clothing",
          "john varvatos (company)": "clothing", "johnny cupcakes": "clothing", "johnston & murphy": "clothing",
          "jordache": "clothing", "jovani fashion": "clothing", "jovovich-hawk": "clothing",
          "juicy couture": "clothing", "karen kane": "clothing", "kani ladies": "clothing", "karmaloop": "clothing",
          "kate spade & company": "clothing", "kenneth cole productions": "clothing",
          "alan king (designer)": "clothing", "kühl (clothing)": "clothing", "l.a.m.b.": "clothing",
          "l.e.i.": "clothing", "l.l.bean": "clothing", "l.l.bean signature": "clothing",
          "la denim atelier": "clothing", "lands' end": "clothing", "le tigre (clothing brand)": "clothing",
          "lee (jeans)": "clothing", "level 27 clothing": "clothing", "levi strauss & co.": "clothing",
          "lids (store)": "clothing", "lifted research group": "clothing", "lilli ann": "clothing",
          "live breathe futbol": "clothing", "loden dager": "clothing", "los angeles apparel": "clothing",
          "lucky brand jeans": "clothing", "lularoe": "clothing", "macbeth footwear": "clothing",
          "mainbocher": "clothing", "marc anthony collection": "clothing", "marchesa (brand)": "clothing",
          "martin + osa": "clothing", "sid mashburn": "clothing", "massive goods": "clothing", "mataano": "clothing",
          "members only (fashion brand)": "clothing", "metal mulisha": "clothing", "milly (fashion brand)": "clothing",
          "ministry of supply (clothing)": "clothing", "mitchell & ness": "clothing", "mossimo": "clothing",
          "munsingwear": "clothing", "nice collective": "clothing", "no fear": "clothing", "noah (brand)": "clothing",
          "the north face": "clothing", "number lab": "clothing", "oaklandish": "clothing", "ocean pacific": "clothing",
          "old navy": "clothing", "opening ceremony (brand)": "clothing", "original penguin": "clothing",
          "orvis": "clothing"}

distribution = {}

for i in items.keys():
    if i.split()[0] in lookup.keys():
        cat = lookup[i.split()[0]]
        if cat in distribution.keys():
            distribution[cat] += items[i]
        else:
            distribution[cat] = items[i]
    else:
        if 'others' in distribution.keys():
            distribution['others'] += items[i]
        else:
            distribution['others'] = items[i]

fixedList = []
dynamicList = []
categoryList = []

for i in resultList:
    fixedList.append({i: resultList[i]})

for i in items:
    dynamicList.append({i: items[i]})

for i in distribution:
    categoryList.append({i: distribution[i]})

finalResult = {"Fixed": fixedList, "Items": dynamicList, "Category": categoryList}
finalResult = json.dumps(finalResult)
print(finalResult)
sys.stdout.flush()

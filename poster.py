import json
import time
import random
from datetime import datetime, timezone
from supabase import create_client, Client
from urllib.parse import urlparse, urlencode, parse_qsl
import re
import requests
import os
from mistralai.client import Mistral
# ==========================================
# 1. API Keys & Database Setup
# ==========================================
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]

mistral_client = Mistral(
    api_key=MISTRAL_API_KEY,
)
# Supabase credentials:
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
COMPANY_LIMIT_FILE = "company_limit.txt"
MAX_JOBS_PER_COMPANY = 4
# Central Files
TARGET_FILE = "automatic.txt"
SEEN_JOBS_FILE = "seen_jobs.txt"
ALERT_TRACKING_FILE = "alertcountries.txt"
MUST_SEEN_FILE = "must_seen.txt"



# ==========================================
# 2. Categories Data & Mappings
# ==========================================
CATEGORIES_MAP = {
    "Development": ["React", "Next.js", "Node.js", "Python", "MERN Stack", "WordPress", "Shopify", "Web3", "Frontend", "Backend", "DevOps", "Cybersecurity", "QA Engineer", "Automation Engineer", "Game Dev"],
    "Mobile App": ["React Native", "Flutter", "iOS", "Swift", "Android", "Kotlin", "Ionic", "App Design"],
    "AI & Machine Learning": ["AI Engineer", "Machine Learning", "NLP", "Computer Vision", "Prompt Engineering", "Chatbot Dev", "TensorFlow", "OpenAI API", "Python Scripting"],
    "Design & Creative": ["UI/UX Design", "Graphic Design", "Logo Design", "Figma", "Adobe Photoshop", "Illustrator", "Packaging Design", "Presentation Design", "NFT Art"],
    "Video & Animation": ["Video Editor", "Premiere Pro", "After Effects", "Motion Graphics", "3D Animation", "Thumbnail Artist", "Short Form (Reels/TikTok)", "VFX"],
    "Audio & Voice": ["Voice Over", "Audio Engineering", "Podcast Editor", "Music Production", "Sound Design", "Mixing & Mastering"],
    "Writing & Translation": ["Content Writer", "Copywriter", "Technical Writer", "Ghostwriter", "Proofreading", "Translation", "Scriptwriting", "Blog Writing", "Resume Writing"],
    "Marketing & Sales": ["SEO", "Social Media Manager", "Facebook Ads", "Google Ads", "Email Marketing", "Lead Generation", "Sales Representative", "Cold Calling", "Affiliate Marketing", "Influencer Marketing"],
    "Admin & Support": ["Virtual Assistant", "Data Entry", "Executive Assistant", "Research", "Project Management", "Transcription", "Spreadsheets (Excel/Google Sheets)"],
    "Customer Service": ["Customer Support", "Technical Support", "Community Manager", "Chat Support", "Call Center", "Zendesk"],
    "Finance & Accounting": ["Accountant", "Bookkeeping", "Financial Analyst", "Tax Preparation", "QuickBooks", "Xero", "CFO", "Crypto Trading"],
    "Legal & HR": ["Legal Consultant", "Contract Law", "Paralegal", "Recruiter", "HR Manager", "Talent Acquisition"],
    "Education & Coaching": ["Online Tutor", "Course Creator", "Language Teacher", "Math Tutor", "Coding Mentor", "Fitness Coach", "Life Coach"],
    "Data Science & Analytics": ["Data Scientist", "Data Analyst", "Business Intelligence", "Power BI", "Tableau", "SQL", "Big Data", "Data Scraping"],
    "Engineering & Architecture": ["CAD Designer", "3D Modeling", "Interior Design", "Mechanical Engineering", "Electrical Engineering", "AutoCAD", "SolidWorks"]
}

COUNTRY_MAPPING = {
    "afghanistan": "Afghanistan", "af": "Afghanistan", "albania": "Albania", "al": "Albania", "algeria": "Algeria", "dz": "Algeria",
    "andorra": "Andorra", "ad": "Andorra", "angola": "Angola", "ao": "Angola", "antigua and barbuda": "Antigua and Barbuda", "ag": "Antigua and Barbuda",
    "argentina": "Argentina", "ar": "Argentina", "armenia": "Armenia", "am": "Armenia", "australia": "Australia", "au": "Australia", "oz": "Australia",
    "austria": "Austria", "at": "Austria", "azerbaijan": "Azerbaijan", "az": "Azerbaijan", "bahamas": "Bahamas", "bs": "Bahamas",
    "the bahamas": "Bahamas", "bahrain": "Bahrain", "bh": "Bahrain", "bangladesh": "Bangladesh", "bd": "Bangladesh", "barbados": "Barbados", "bb": "Barbados",
    "belarus": "Belarus", "by": "Belarus", "belgium": "Belgium", "be": "Belgium", "belize": "Belize", "bz": "Belize", "benin": "Benin", "bj": "Benin",
    "bhutan": "Bhutan", "bt": "Bhutan", "bolivia": "Bolivia", "bo": "Bolivia", "bosnia and herzegovina": "Bosnia and Herzegovina", "ba": "Bosnia and Herzegovina",
    "bosnia": "Bosnia and Herzegovina", "botswana": "Botswana", "bw": "Botswana", "brazil": "Brazil", "br": "Brazil", "brunei": "Brunei", "bn": "Brunei",
    "bulgaria": "Bulgaria", "bg": "Bulgaria", "burkina faso": "Burkina Faso", "bf": "Burkina Faso", "burundi": "Burundi", "bi": "Burundi",
    "cabo verde": "Cabo Verde", "cv": "Cabo Verde", "cape verde": "Cabo Verde", "cambodia": "Cambodia", "kh": "Cambodia", "cameroon": "Cameroon", "cm": "Cameroon",
    "canada": "Canada", "ca": "Canada", "central african republic": "Central African Republic", "cf": "Central African Republic", "car": "Central African Republic",
    "chad": "Chad", "td": "Chad", "chile": "Chile", "cl": "Chile", "china": "China", "cn": "China", "prc": "China", "colombia": "Colombia", "co": "Colombia",
    "comoros": "Comoros", "km": "Comoros", "congo (brazzaville)": "Congo", "cg": "Congo", "congo": "Congo", "republic of the congo": "Congo",
    "congo (kinshasa)": "Democratic Republic of the Congo", "cd": "Democratic Republic of the Congo", "drc": "Democratic Republic of the Congo",
    "dr congo": "Democratic Republic of the Congo", "costa rica": "Costa Rica", "cr": "Costa Rica", "croatia": "Croatia", "hr": "Croatia",
    "cuba": "Cuba", "cu": "Cuba", "cyprus": "Cyprus", "cy": "Cyprus", "czechia": "Czechia", "cz": "Czechia", "czech republic": "Czechia",
    "denmark": "Denmark", "dk": "Denmark", "djibouti": "Djibouti", "dj": "Djibouti", "dominica": "Dominica", "dm": "Dominica",
    "dominican republic": "Dominican Republic", "do": "Dominican Republic", "ecuador": "Ecuador", "ec": "Ecuador", "egypt": "Egypt", "eg": "Egypt",
    "el salvador": "El Salvador", "sv": "El Salvador", "equatorial guinea": "Equatorial Guinea", "gq": "Equatorial Guinea", "eritrea": "Eritrea", "er": "Eritrea",
    "estonia": "Estonia", "ee": "Estonia", "eswatini": "Eswatini", "sz": "Eswatini", "swaziland": "Eswatini", "ethiopia": "Ethiopia", "et": "Ethiopia",
    "fiji": "Fiji", "fj": "Fiji", "finland": "Finland", "fi": "Finland", "france": "France", "fr": "France", "gabon": "Gabon", "ga": "Gabon",
    "gambia": "Gambia", "gm": "Gambia", "the gambia": "Gambia", "georgia": "Georgia", "ge": "Georgia", "germany": "Germany", "de": "Germany",
    "ghana": "Ghana", "gh": "Ghana", "greece": "Greece", "gr": "Greece", "grenada": "Grenada", "gd": "Grenada", "guatemala": "Guatemala", "gt": "Guatemala",
    "guinea": "Guinea", "gn": "Guinea", "guinea-bissau": "Guinea-Bissau", "gw": "Guinea-Bissau", "guyana": "Guyana", "gy": "Guyana",
    "haiti": "Haiti", "ht": "Haiti", "honduras": "Honduras", "hn": "Honduras", "hungary": "Hungary", "hu": "Hungary", "iceland": "Iceland", "is": "Iceland",
    "india": "India", "in": "India", "indonesia": "Indonesia", "id": "Indonesia", "iran": "Iran", "ir": "Iran", "islamic republic of iran": "Iran",
    "iraq": "Iraq", "iq": "Iraq", "ireland": "Ireland", "ie": "Ireland", "republic of ireland": "Ireland", "israel": "Israel", "il": "Israel",
    "italy": "Italy", "it": "Italy", "ivory coast": "Ivory Coast", "ci": "Ivory Coast", "cote d'ivoire": "Ivory Coast", "côte d'ivoire": "Ivory Coast",
    "jamaica": "Jamaica", "jm": "Jamaica", "japan": "Japan", "jp": "Japan", "jordan": "Jordan", "jo": "Jordan", "kazakhstan": "Kazakhstan", "kz": "Kazakhstan",
    "kenya": "Kenya", "ke": "Kenya", "kiribati": "Kiribati", "ki": "Kiribati", "kuwait": "Kuwait", "kw": "Kuwait", "kyrgyzstan": "Kyrgyzstan", "kg": "Kyrgyzstan",
    "laos": "Laos", "la": "Laos", "lao pdr": "Laos", "latvia": "Latvia", "lv": "Latvia", "lebanon": "Lebanon", "lb": "Lebanon", "lesotho": "Lesotho", "ls": "Lesotho",
    "liberia": "Liberia", "lr": "Liberia", "libya": "Libya", "ly": "Libya", "liechtenstein": "Liechtenstein", "li": "Liechtenstein", "lithuania": "Lithuania", "lt": "Lithuania",
    "luxembourg": "Luxembourg", "lu": "Luxembourg", "madagascar": "Madagascar", "mg": "Madagascar", "malawi": "Malawi", "mw": "Malawi", "malaysia": "Malaysia", "my": "Malaysia",
    "maldives": "Maldives", "mv": "Maldives", "mali": "Mali", "ml": "Mali", "malta": "Malta", "mt": "Malta", "marshall islands": "Marshall Islands", "mh": "Marshall Islands",
    "mauritania": "Mauritania", "mr": "Mauritania", "mauritius": "Mauritius", "mu": "Mauritius", "mexico": "Mexico", "mx": "Mexico", "micronesia": "Micronesia", "fm": "Micronesia",
    "fs micronesia": "Micronesia", "moldova": "Moldova", "md": "Moldova", "republic of moldova": "Moldova", "monaco": "Monaco", "mc": "Monaco", "mongolia": "Mongolia", "mn": "Mongolia",
    "montenegro": "Montenegro", "me": "Montenegro", "morocco": "Morocco", "ma": "Morocco", "mozambique": "Mozambique", "mz": "Mozambique", "myanmar": "Myanmar", "mm": "Myanmar",
    "burma": "Myanmar", "namibia": "Namibia", "na": "Namibia", "nauru": "Nauru", "nr": "Nauru", "nepal": "Nepal", "np": "Nepal", "netherlands": "Netherlands", "nl": "Netherlands",
    "holland": "Netherlands", "the netherlands": "Netherlands", "new zealand": "New Zealand", "nz": "New Zealand", "nicaragua": "Nicaragua", "ni": "Nicaragua",
    "niger": "Niger", "ne": "Niger", "nigeria": "Nigeria", "ng": "Nigeria", "north korea": "North Korea", "kp": "North Korea", "dprk": "North Korea",
    "north macedonia": "North Macedonia", "mk": "North Macedonia", "macedonia": "North Macedonia", "norway": "Norway", "no": "Norway", "oman": "Oman", "om": "Oman",
    "pakistan": "Pakistan", "pk": "Pakistan", "pak": "Pakistan", "palau": "Palau", "pw": "Palau", "palestine": "Palestine", "ps": "Palestine", "state of palestine": "Palestine",
    "panama": "Panama", "pa": "Panama", "papua new guinea": "Papua New Guinea", "pg": "Papua New Guinea", "png": "Papua New Guinea", "paraguay": "Paraguay", "py": "Paraguay",
    "peru": "Peru", "pe": "Peru", "philippines": "Philippines", "ph": "Philippines", "the philippines": "Philippines", "poland": "Poland", "pl": "Poland",
    "portugal": "Portugal", "pt": "Portugal", "qatar": "Qatar", "qa": "Qatar", "romania": "Romania", "ro": "Romania", "russia": "Russia", "ru": "Russia",
    "russian federation": "Russia", "rwanda": "Rwanda", "rw": "Rwanda", "saint kitts and nevis": "Saint Kitts and Nevis", "kn": "Saint Kitts and Nevis",
    "st kitts and nevis": "Saint Kitts and Nevis", "saint lucia": "Saint Lucia", "lc": "Saint Lucia", "st lucia": "Saint Lucia", "saint vincent and the grenadines": "Saint Vincent and the Grenadines",
    "vc": "Saint Vincent and the Grenadines", "st vincent": "Saint Vincent and the Grenadines", "samoa": "Samoa", "ws": "Samoa", "san marino": "San Marino", "sm": "San Marino",
    "sao tome and principe": "Sao Tome and Principe", "st": "Sao Tome and Principe", "saudi arabia": "Saudi Arabia", "sa": "Saudi Arabia", "ksa": "Saudi Arabia",
    "senegal": "Senegal", "sn": "Senegal", "serbia": "Serbia", "rs": "Serbia", "seychelles": "Seychelles", "sc": "Seychelles", "sierra leone": "Sierra Leone", "sl": "Sierra Leone",
    "singapore": "Singapore", "sg": "Singapore", "slovakia": "Slovakia", "sk": "Slovakia", "slovak republic": "Slovakia", "slovenia": "Slovenia", "si": "Slovenia",
    "solomon islands": "Solomon Islands", "sb": "Solomon Islands", "somalia": "Somalia", "so": "Somalia", "south africa": "South Africa", "za": "South Africa",
    "rsa": "South Africa", "south korea": "South Korea", "kr": "South Korea", "rok": "South Korea", "south sudan": "South Sudan", "ss": "South Sudan",
    "spain": "Spain", "es": "Spain", "sri lanka": "Sri Lanka", "lk": "Sri Lanka", "sudan": "Sudan", "sd": "Sudan", "suriname": "Suriname", "sr": "Suriname",
    "sweden": "Sweden", "se": "Sweden", "switzerland": "Switzerland", "ch": "Switzerland", "syria": "Syria", "sy": "Syria", "syrian arab republic": "Syria",
    "taiwan": "Taiwan", "tw": "Taiwan", "republic of china": "Taiwan", "roc": "Taiwan", "tajikistan": "Tajikistan", "tj": "Tajikistan", "tanzania": "Tanzania", "tz": "Tanzania",
    "thailand": "Thailand", "th": "Thailand", "timor-leste": "Timor-Leste", "tl": "Timor-Leste", "east timor": "Timor-Leste", "togo": "Togo", "tg": "Togo",
    "tonga": "Tonga", "to": "Tonga", "trinidad and tobago": "Trinidad and Tobago", "tt": "Trinidad and Tobago", "trinidad": "Trinidad and Tobago", "tunisia": "Tunisia", "tn": "Tunisia",
    "turkey": "Turkey", "tr": "Turkey", "türkiye": "Turkey", "turkmenistan": "Turkmenistan", "tm": "Turkmenistan", "tuvalu": "Tuvalu", "tv": "Tuvalu",
    "uganda": "Uganda", "ug": "Uganda", "ukraine": "Ukraine", "ua": "Ukraine", "united arab emirates": "United Arab Emirates", "ae": "United Arab Emirates",
    "uae": "United Arab Emirates", "united kingdom": "United Kingdom", "gb": "United Kingdom", "uk": "United Kingdom", "great britain": "United Kingdom",
    "britain": "United Kingdom", "united states": "United States", "us": "United States", "usa": "United States", "united states of america": "United States",
    "america": "United States", "uruguay": "Uruguay", "uy": "Uruguay", "uzbekistan": "Uzbekistan", "uz": "Uzbekistan", "vanuatu": "Vanuatu", "vu": "Vanuatu",
    "vatican city": "Vatican City", "va": "Vatican City", "holy see": "Vatican City", "venezuela": "Venezuela", "ve": "Venezuela", "vietnam": "Vietnam",
    "vn": "Vietnam", "viet nam": "Vietnam", "yemen": "Yemen", "ye": "Yemen", "zambia": "Zambia", "zm": "Zambia", "zimbabwe": "Zimbabwe", "zw": "Zimbabwe"
}

# ==========================================
# 2b. City -> Country Data (for city-level location matching)
# ==========================================
COUNTRY_CITIES = {
    "Afghanistan": ["Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad", "Kunduz", "Ghazni", "Balkh", "Puli Khumri", "Charikar", "Sheberghan", "Khost", "Lashkar Gah", "Taloqan", "Zaranj", "Bamyan", "Farah", "Maidan Shar", "Gardez", "Asadabad"],
    "Albania": ["Tirana", "Durres", "Vlore", "Shkoder", "Elbasan", "Korce", "Fier", "Berat", "Lushnje", "Kavaje", "Gjirokaster", "Sarande", "Pogradec", "Kukes", "Lezhe", "Peshkopi", "Kruje", "Burrel", "Fushe-Kruje", "Patos"],
    "Algeria": ["Algiers", "Oran", "Constantine", "Annaba", "Blida", "Batna", "Setif", "Sidi Bel Abbes", "Biskra", "Tebessa", "Tlemcen", "Bejaia", "Skikda", "Tiaret", "Ouargla", "Bordj Bou Arreridj", "Chlef", "Djelfa", "Ghardaia", "Mostaganem"],
    "Andorra": ["Andorra la Vella", "Escaldes-Engordany", "Encamp", "Sant Julia de Loria", "La Massana", "Ordino", "Canillo", "Arinsal", "Pas de la Casa", "El Serrat", "Soldeu", "Erts", "La Cortinada", "Anyos", "Sispony", "Llorts", "Ransol", "Bixessarri", "Aixovall", "Aixirivall"],
    "Angola": ["Luanda", "Huambo", "Lobito", "Benguela", "Lubango", "Kuito", "Malanje", "Namibe", "Soyo", "Cabinda", "Uige", "Saurimo", "Sumbe", "Menongue", "Ondjiva", "Caxito", "Dundo", "Luena", "Camacupa", "Xangongo"],
    "Antigua and Barbuda": ["St. John's", "All Saints", "Liberta", "Potter's Village", "Bolans", "Swetes", "Parham", "Falmouth", "Codrington", "Freetown", "Piggotts", "Willikies", "Seaview Farm", "English Harbour", "Old Road", "Urlings", "Cedar Grove", "Bendals", "Sea View Farm", "Jennings"],
    "Argentina": ["Buenos Aires", "Cordoba", "Rosario", "Mendoza", "La Plata", "San Miguel de Tucuman", "Mar del Plata", "Salta", "Santa Fe", "San Juan", "Resistencia", "Neuquen", "Santiago del Estero", "Corrientes", "Posadas", "San Salvador de Jujuy", "Bahia Blanca", "Parana", "Formosa", "Ushuaia"],
    "Armenia": ["Yerevan", "Gyumri", "Vanadzor", "Vagharshapat", "Hrazdan", "Abovyan", "Kapan", "Armavir", "Gavar", "Artashat", "Ijevan", "Charentsavan", "Sevan", "Ashtarak", "Goris", "Masis", "Stepanavan", "Dilijan", "Spitak", "Alaverdi"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra", "Newcastle", "Wollongong", "Hobart", "Geelong", "Townsville", "Cairns", "Darwin", "Toowoomba", "Ballarat", "Bendigo", "Launceston", "Mackay", "Rockhampton"],
    "Austria": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt", "Villach", "Wels", "Sankt Polten", "Dornbirn", "Wiener Neustadt", "Steyr", "Feldkirch", "Bregenz", "Leonding", "Klosterneuburg", "Baden", "Wolfsberg", "Leoben", "Krems"],
    "Azerbaijan": ["Baku", "Ganja", "Sumqayit", "Mingachevir", "Nakhchivan", "Shirvan", "Sheki", "Yevlakh", "Khankendi", "Lankaran", "Naftalan", "Shamakhi", "Guba", "Barda", "Zaqatala", "Gabala", "Salyan", "Agdam", "Imishli", "Goychay"],
    "Bahamas": ["Nassau", "Freeport", "West End", "Coopers Town", "Marsh Harbour", "High Rock", "Andros Town", "Fresh Creek", "George Town", "Alice Town", "Spanish Wells", "Dunmore Town", "Rock Sound", "Governor's Harbour", "Cockburn Town", "Matthew Town", "Clarence Town", "Arthur's Town", "Nichollstown", "Bimini"],
    "Bahrain": ["Manama", "Riffa", "Muharraq", "Hamad Town", "A'ali", "Isa Town", "Sitra", "Budaiya", "Jidhafs", "Al-Malikiyah", "Zallaq", "Karranah", "Sanabis", "Tubli", "Sanad", "Al Hidd", "Askar", "Duraz", "Jasra", "Nuwaidrat"],
    "Bangladesh": ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Sylhet", "Barisal", "Rangpur", "Comilla", "Mymensingh", "Narayanganj", "Gazipur", "Jessore", "Bogra", "Dinajpur", "Tangail", "Cox's Bazar", "Pabna", "Feni", "Brahmanbaria", "Kushtia"],
    "Barbados": ["Bridgetown", "Speightstown", "Oistins", "Bathsheba", "Holetown", "Crane", "Six Cross Roads", "Bayfield", "Blackmans", "Bagatelle", "Checker Hall", "Crab Hill", "Half Moon Fort", "Boscobel", "Cave Hill", "Warrens", "Hastings", "Worthing", "Welches", "Prospect"],
    "Belarus": ["Minsk", "Gomel", "Mogilev", "Vitebsk", "Grodno", "Brest", "Babruysk", "Baranovichi", "Borisov", "Pinsk", "Orsha", "Mozyr", "Soligorsk", "Novopolotsk", "Lida", "Molodechno", "Polotsk", "Zhlobin", "Svetlogorsk", "Rechitsa"],
    "Belgium": ["Brussels", "Antwerp", "Ghent", "Charleroi", "Liege", "Bruges", "Namur", "Leuven", "Mons", "Aalst", "Mechelen", "Kortrijk", "Hasselt", "Sint-Niklaas", "Ostend", "Tournai", "Genk", "Seraing", "Roeselare", "Verviers"],
    "Belize": ["Belize City", "San Ignacio", "Orange Walk", "Belmopan", "Dangriga", "Corozal", "San Pedro", "Punta Gorda", "Benque Viejo", "Valley of Peace", "Ladyville", "Burrell Boom", "Hopkins", "Placencia", "Independence", "Santa Elena", "Shipyard", "Cayo", "Blue Creek", "Bomba"],
    "Benin": ["Cotonou", "Porto-Novo", "Parakou", "Djougou", "Bohicon", "Kandi", "Lokossa", "Ouidah", "Abomey", "Natitingou", "Save", "Nikki", "Pobe", "Kandi", "Malanville", "Aplahoue", "Come", "Ze", "Segbana", "Dassa-Zoume"],
    "Bhutan": ["Thimphu", "Phuntsholing", "Punakha", "Paro", "Gelephu", "Samdrup Jongkhar", "Trashigang", "Wangdue Phodrang", "Mongar", "Jakar", "Trongsa", "Samtse", "Haa", "Lhuentse", "Pemagatshel", "Trashiyangtse", "Zhemgang", "Dagana", "Sarpang", "Gasa"],
    "Bolivia": ["La Paz", "Santa Cruz de la Sierra", "Cochabamba", "Sucre", "Oruro", "Tarija", "Potosi", "Sacaba", "Quillacollo", "Montero", "Trinidad", "Riberalta", "Yacuiba", "Villazon", "Camiri", "Cobija", "El Alto", "Warnes", "Guayaramerin", "Uyuni"],
    "Bosnia and Herzegovina": ["Sarajevo", "Banja Luka", "Tuzla", "Zenica", "Mostar", "Bijeljina", "Brcko", "Prijedor", "Doboj", "Cazin", "Bihac", "Gradiska", "Trebinje", "Zvornik", "Visoko", "Gorazde", "Konjic", "Livno", "Zenica", "Travnik"],
    "Botswana": ["Gaborone", "Francistown", "Molepolole", "Selebi-Phikwe", "Maun", "Serowe", "Kanye", "Mahalapye", "Mochudi", "Mogoditshane", "Lobatse", "Palapye", "Ramotswa", "Tlokweng", "Letlhakane", "Ghanzi", "Tonota", "Jwaneng", "Kasane", "Orapa"],
    "Brazil": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza", "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre", "Belem", "Goiania", "Guarulhos", "Campinas", "Sao Luis", "Sao Goncalo", "Maceio", "Duque de Caxias", "Natal", "Teresina"],
    "Brunei": ["Bandar Seri Begawan", "Kuala Belait", "Seria", "Tutong", "Bangar", "Muara", "Serasa", "Kilanas", "Lumapas", "Sengkurong", "Berakas", "Kota Batu", "Jerudong", "Tanjong Maya", "Rimba", "Lambak", "Mentiri", "Pekan Muara", "Sungai Liang", "Panaga"],
    "Bulgaria": ["Sofia", "Plovdiv", "Varna", "Burgas", "Ruse", "Stara Zagora", "Pleven", "Sliven", "Dobrich", "Shumen", "Pernik", "Haskovo", "Yambol", "Pazardzhik", "Blagoevgrad", "Veliko Tarnovo", "Vratsa", "Gabrovo", "Vidin", "Kazanlak"],
    "Burkina Faso": ["Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Ouahigouya", "Banfora", "Kaya", "Fada N'Gourma", "Dedougou", "Tenkodogo", "Reo", "Manga", "Gaoua", "Dori", "Ziniare", "Diebougou", "Koupela", "Nouna", "Djibo", "Sebba", "Yako"],
    "Burundi": ["Bujumbura", "Gitega", "Muyinga", "Ngozi", "Ruyigi", "Kayanza", "Rutana", "Bururi", "Cankuzo", "Muramvya", "Karuzi", "Kirundo", "Rumonge", "Bubanza", "Cibitoke", "Mwaro", "Makamba", "Isale", "Nyanza-Lac", "Buhiga"],
    "Cabo Verde": ["Praia", "Mindelo", "Santa Maria", "Assomada", "Espargos", "Porto Novo", "Pedra Badejo", "Tarrafal", "Sao Filipe", "Ribeira Grande", "Sal Rei", "Vila do Maio", "Cova Figueira", "Ponta do Sol", "Calheta", "Pombas", "Ribeira Brava", "Nova Sintra", "Sao Domingos", "Picos"],
    "Cambodia": ["Phnom Penh", "Siem Reap", "Battambang", "Sihanoukville", "Poipet", "Kampong Cham", "Kampong Speu", "Ta Khmau", "Pursat", "Kampot", "Kratie", "Kampong Thom", "Prey Veng", "Svay Rieng", "Stung Treng", "Banlung", "Sisophon", "Koh Kong", "Bavet", "Paoy Paet"],
    "Cameroon": ["Douala", "Yaounde", "Garoua", "Bamenda", "Maroua", "Bafoussam", "Ngaoundere", "Bertoua", "Loum", "Kumba", "Edea", "Kumbo", "Buea", "Nkongsamba", "Foumban", "Limbe", "Ebolowa", "Dschang", "Mbouda", "Guider"],
    "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg", "Quebec City", "Hamilton", "Kitchener", "London", "Victoria", "Halifax", "Saskatoon", "Regina", "St. John's", "Windsor", "Oshawa", "Barrie", "Sherbrooke"],
    "Central African Republic": ["Bangui", "Bimbo", "Berberati", "Carnot", "Bambari", "Bouar", "Bossangoa", "Bria", "Bangassou", "Nola", "Kaga-Bandoro", "Sibut", "Mbaiki", "Bozoum", "Zemio", "Batangafo", "Bocaranga", "Obo", "Ndele", "Alindao"],
    "Chad": ["N'Djamena", "Moundou", "Sarh", "Abeche", "Kelo", "Koumra", "Pala", "Am Timan", "Bongor", "Mongo", "Doba", "Ati", "Oum Hadjer", "Massaguet", "Bol", "Faya-Largeau", "Mao", "Biltine", "Fianga", "Lai"],
    "Chile": ["Santiago", "Valparaiso", "Concepcion", "La Serena", "Antofagasta", "Temuco", "Rancagua", "Talca", "Arica", "Chillan", "Iquique", "Puerto Montt", "Coquimbo", "Osorno", "Valdivia", "Punta Arenas", "Copiapo", "Quillota", "Curico", "Calama"],
    "China": ["Shanghai", "Beijing", "Guangzhou", "Shenzhen", "Chengdu", "Chongqing", "Tianjin", "Wuhan", "Xi'an", "Hangzhou", "Nanjing", "Suzhou", "Qingdao", "Dalian", "Zhengzhou", "Shenyang", "Kunming", "Xiamen", "Harbin", "Changsha"],
    "Colombia": ["Bogota", "Medellin", "Cali", "Barranquilla", "Cartagena", "Cucuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibague", "Manizales", "Villavicencio", "Pasto", "Monteria", "Valledupar", "Armenia", "Neiva", "Sincelejo", "Popayan", "Tunja"],
    "Comoros": ["Moroni", "Mutsamudu", "Fomboni", "Domoni", "Tsimbeo", "Ouani", "Mitsamiouli", "Sima", "Adda-Doueni", "Mramani", "Mirontsi", "Chindini", "Iconi", "Mbeni", "Foumbouni", "Dembeni", "Bambao", "Vouani", "Koni-Djodjo", "Tsembehou"],
    "Congo": ["Brazzaville", "Pointe-Noire", "Dolisie", "Nkayi", "Ouesso", "Owando", "Madingou", "Sibiti", "Impfondo", "Kinkala", "Loandjili", "Mossendjo", "Djambala", "Gamboma", "Ewo", "Makoua", "Zanaga", "Mossaka", "Kayes", "Loudima"],
    "Democratic Republic of the Congo": ["Kinshasa", "Lubumbashi", "Mbuji-Mayi", "Kananga", "Kisangani", "Bukavu", "Tshikapa", "Kolwezi", "Likasi", "Goma", "Kikwit", "Uvira", "Bunia", "Matadi", "Mbandaka", "Isiro", "Kalemie", "Kindu", "Gemena", "Butembo"],
    "Costa Rica": ["San Jose", "Alajuela", "Cartago", "Heredia", "Liberia", "Puntarenas", "Limon", "San Isidro", "Desamparados", "Golfito", "Grecia", "San Ramon", "Turrialba", "Nicoya", "Paraiso", "Ciudad Quesada", "Palmares", "Naranjo", "Jaco", "Guapiles"],
    "Croatia": ["Zagreb", "Split", "Rijeka", "Osijek", "Zadar", "Slavonski Brod", "Pula", "Sesvete", "Karlovac", "Sisak", "Varazdin", "Sibenik", "Dubrovnik", "Bjelovar", "Kastela", "Samobor", "Vinkovci", "Koprivnica", "Pozega", "Zabok"],
    "Cuba": ["Havana", "Santiago de Cuba", "Camaguey", "Holguin", "Guantanamo", "Santa Clara", "Bayamo", "Cienfuegos", "Pinar del Rio", "Matanzas", "Ciego de Avila", "Las Tunas", "Sancti Spiritus", "Manzanillo", "Cardenas", "Moron", "Nueva Gerona", "Trinidad", "Baracoa", "Palma Soriano"],
    "Cyprus": ["Nicosia", "Limassol", "Larnaca", "Famagusta", "Paphos", "Kyrenia", "Paralimni", "Aradippou", "Strovolos", "Lakatamia", "Geri", "Dali", "Ergates", "Morphou", "Polis", "Peyia", "Xylofagou", "Deryneia", "Athienou", "Yeroskipou"],
    "Czechia": ["Prague", "Brno", "Ostrava", "Plzen", "Liberec", "Olomouc", "Ceske Budejovice", "Hradec Kralove", "Usti nad Labem", "Pardubice", "Havirov", "Zlin", "Kladno", "Most", "Karvina", "Frydek-Mistek", "Opava", "Decin", "Teplice", "Karlovy Vary"],
    "Denmark": ["Copenhagen", "Aarhus", "Odense", "Aalborg", "Esbjerg", "Randers", "Kolding", "Horsens", "Vejle", "Roskilde", "Herning", "Silkeborg", "Naestved", "Fredericia", "Viborg", "Koge", "Holstebro", "Taastrup", "Slagelse", "Hillerod"],
    "Djibouti": ["Djibouti City", "Ali Sabieh", "Tadjourah", "Obock", "Dikhil", "Arta", "Holhol", "Yoboki", "Randa", "As Eyla", "Balho", "Galafi", "Loyada", "We'a", "Alaili Dadda", "Damerjog", "Khor Angar", "Doraleh", "Chabelley", "Ali Adde"],
    "Dominica": ["Roseau", "Portsmouth", "Marigot", "Berekua", "Mahaut", "Wesley", "St. Joseph", "Pointe Michel", "Grand Bay", "Salisbury", "Castle Bruce", "Colihaut", "Vieille Case", "Soufriere", "La Plaine", "Calibishie", "Layou", "Wotten Waven", "Bagatelle", "Fond St. Jean"],
    "Dominican Republic": ["Santo Domingo", "Santiago", "La Romana", "San Pedro de Macoris", "San Cristobal", "Puerto Plata", "La Vega", "Higuey", "San Francisco de Macoris", "Bani", "Barahona", "Moca", "Bonao", "Azua", "Mao", "Cotui", "Nagua", "Bavaro", "Constanza", "Jarabacoa"],
    "Ecuador": ["Quito", "Guayaquil", "Cuenca", "Santo Domingo", "Machala", "Duran", "Manta", "Portoviejo", "Loja", "Ambato", "Esmeraldas", "Quevedo", "Riobamba", "Milagro", "Ibarra", "La Libertad", "Babahoyo", "Latacunga", "Tulcan", "Sangolqui"],
    "Egypt": ["Cairo", "Alexandria", "Giza", "Shubra El Kheima", "Port Said", "Suez", "Luxor", "Mansoura", "Tanta", "Asyut", "Ismailia", "Faiyum", "Zagazig", "Aswan", "Damietta", "Damanhur", "Minya", "Beni Suef", "Qena", "Sohag"],
    "El Salvador": ["San Salvador", "Santa Ana", "San Miguel", "Soyapango", "Mejicanos", "Santa Tecla", "Apopa", "Delgado", "Sonsonate", "Ahuachapan", "Usulutan", "San Vicente", "La Union", "Zacatecoluca", "Cojutepeque", "Chalatenango", "Chalchuapa", "Ilobasco", "Metapan", "Acajutla"],
    "Equatorial Guinea": ["Malabo", "Bata", "Ebebiyin", "Aconibe", "Anisoc", "Luba", "Evinayong", "Mongomo", "Rebola", "Mikomeseng", "Nsork", "Riaba", "Micomeseng", "Niefang", "Cogo", "Añisoc", "Machinda", "Basakato", "Bicurga", "Corisco"],
    "Eritrea": ["Asmara", "Keren", "Massawa", "Assab", "Mendefera", "Barentu", "Adi Keyh", "Adi Quala", "Dekemhare", "Ghinda", "Segeneyti", "Teseney", "Nakfa", "Senafe", "Agordat", "Akordat", "Tio", "Foro", "Karora", "Digsa"],
    "Estonia": ["Tallinn", "Tartu", "Narva", "Parnu", "Kohtla-Jarve", "Viljandi", "Rakvere", "Maardu", "Kuressaare", "Sillamae", "Voru", "Valga", "Haapsalu", "Jogeva", "Keila", "Paide", "Elva", "Tapa", "Polva", "Saue"],
    "Eswatini": ["Mbabane", "Manzini", "Big Bend", "Malkerns", "Nhlangano", "Piggs Peak", "Siteki", "Lobamba", "Hluti", "Simunye", "Mhlume", "Ezulwini", "Bhunya", "Kwaluseni", "Matsapha", "Sithobela", "Tshaneni", "Lavumisa", "Mankayane", "Bulembu"],
    "Ethiopia": ["Addis Ababa", "Dire Dawa", "Mekelle", "Gondar", "Adama", "Bahir Dar", "Hawassa", "Jimma", "Jijiga", "Shashamane", "Bishoftu", "Sodo", "Arba Minch", "Hosaena", "Dessie", "Nekemte", "Debre Birhan", "Asella", "Gambela", "Harar"],
    "Fiji": ["Suva", "Lautoka", "Nadi", "Labasa", "Ba", "Levuka", "Sigatoka", "Savusavu", "Nausori", "Tavua", "Rakiraki", "Navua", "Korovou", "Lami", "Nabouwalu", "Vatukoula", "Ba", "Deuba", "Pacific Harbour", "Korolevu"],
    "Finland": ["Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu", "Turku", "Jyvaskyla", "Lahti", "Kuopio", "Pori", "Kouvola", "Joensuu", "Lappeenranta", "Hameenlinna", "Vaasa", "Seinajoki", "Rovaniemi", "Mikkeli", "Kotka", "Salo"],
    "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes", "Reims", "Le Havre", "Saint-Etienne", "Toulon", "Grenoble", "Dijon", "Angers", "Nimes", "Villeurbanne"],
    "Gabon": ["Libreville", "Port-Gentil", "Franceville", "Oyem", "Moanda", "Mouila", "Lambarene", "Tchibanga", "Koulamoutou", "Makokou", "Bitam", "Gamba", "Ndende", "Booue", "Mitzic", "Okondja", "Ntoum", "Fougamou", "Lastoursville", "Mayumba"],
    "Gambia": ["Banjul", "Serekunda", "Brikama", "Bakau", "Farafenni", "Lamin", "Sukuta", "Basse Santa Su", "Gunjur", "Soma", "Janjanbureh", "Kerewan", "Kanifing", "Sanyang", "Barra", "Kuntaur", "Mansa Konko", "Gambissara", "Essau", "Bansang"],
    "Georgia": ["Tbilisi", "Batumi", "Kutaisi", "Rustavi", "Gori", "Zugdidi", "Poti", "Kobuleti", "Khashuri", "Samtredia", "Senaki", "Zestafoni", "Marneuli", "Telavi", "Akhaltsikhe", "Ozurgeti", "Kaspi", "Chiatura", "Tskaltubo", "Sagarejo"],
    "Germany": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Dusseldorf", "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden", "Hanover", "Nuremberg", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Mannheim"],
    "Ghana": ["Accra", "Kumasi", "Tamale", "Sekondi-Takoradi", "Sunyani", "Cape Coast", "Obuasi", "Tema", "Teshie", "Madina", "Koforidua", "Wa", "Ho", "Techiman", "Nkawkaw", "Bolgatanga", "Ashaiman", "Winneba", "Berekum", "Yendi"],
    "Greece": ["Athens", "Thessaloniki", "Patras", "Heraklion", "Larissa", "Volos", "Rhodes", "Ioannina", "Chania", "Chalcis", "Serres", "Alexandroupoli", "Xanthi", "Katerini", "Trikala", "Kavala", "Kalamata", "Kozani", "Corfu", "Drama"],
    "Grenada": ["St. George's", "Gouyave", "Grenville", "Victoria", "Sauteurs", "Hillsborough", "Grand Roy", "St. David's", "Birchgrove", "Concord", "Woburn", "Mount Rose", "Tempe", "Munich", "Constantine", "Belmont", "Beaulieu", "Perdmontemps", "Clozier", "Paradise"],
    "Guatemala": ["Guatemala City", "Mixco", "Villa Nueva", "Quetzaltenango", "Escuintla", "Chinautla", "Cobán", "Huehuetenango", "Chimaltenango", "Amatitlan", "Puerto Barrios", "Retalhuleu", "Mazatenango", "Chichicastenango", "Santa Lucia Cotzumalguapa", "Jalapa", "Zacapa", "Antigua Guatemala", "San Marcos", "Solola"],
    "Guinea": ["Conakry", "Nzerekore", "Kankan", "Kindia", "Labe", "Gueckedou", "Mamou", "Boke", "Faranah", "Kissidougou", "Siguiri", "Dabola", "Dinguiraye", "Telimele", "Macenta", "Kerouane", "Beyla", "Fria", "Kouroussa", "Yomou"],
    "Guinea-Bissau": ["Bissau", "Bafata", "Gabu", "Cacheu", "Bolama", "Catio", "Farim", "Buba", "Mansoa", "Quinhamel", "Bubaque", "Fulacunda", "Canchungo", "Bissora", "Contuboel", "Sao Domingos", "Pitche", "Pirada", "Jabada", "Bambadinca"],
    "Guyana": ["Georgetown", "Linden", "New Amsterdam", "Anna Regina", "Corriverton", "Bartica", "Skeldon", "Rosignol", "Mahaica", "Mabaruma", "Lethem", "Parika", "Vreed-en-Hoop", "Fort Wellington", "Rose Hall", "Whim", "Kwakwani", "Mahdia", "Ituni", "Charity"],
    "Haiti": ["Port-au-Prince", "Cap-Haitien", "Gonaives", "Les Cayes", "Petion-Ville", "Delmas", "Jacmel", "Saint-Marc", "Jeremie", "Fort-Liberte", "Hinche", "Miragoane", "Leogane", "Port-de-Paix", "Croix-des-Bouquets", "Carrefour", "Ouanaminthe", "Limbe", "Petit-Goave", "Anse-a-Veau"],
    "Honduras": ["Tegucigalpa", "San Pedro Sula", "Choloma", "La Ceiba", "El Progreso", "Comayagua", "Puerto Cortes", "Danli", "Choluteca", "Siguatepeque", "Juticalpa", "Villanueva", "Tocoa", "Tela", "Santa Rosa de Copan", "Olanchito", "Yoro", "Catacamas", "Nacaome", "Roatan"],
    "Hungary": ["Budapest", "Debrecen", "Szeged", "Miskolc", "Pecs", "Gyor", "Nyiregyhaza", "Kecskemet", "Szekesfehervar", "Szombathely", "Szolnok", "Tatabanya", "Kaposvar", "Erd", "Veszprem", "Bekescsaba", "Zalaegerszeg", "Sopron", "Eger", "Nagykanizsa"],
    "Iceland": ["Reykjavik", "Kopavogur", "Hafnarfjordur", "Akureyri", "Reykjanesbaer", "Gardabaer", "Mosfellsbaer", "Selfoss", "Akranes", "Fjardabyggd", "Egilsstadir", "Isafjordur", "Vestmannaeyjar", "Borgarnes", "Grindavik", "Husavik", "Saudarkrokur", "Blonduos", "Hveragerdi", "Hofn"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune", "Jaipur", "Surat", "Lucknow", "Kanpur", "Nagpur", "Indore", "Bhopal", "Patna", "Vadodara", "Ludhiana", "Agra", "Varanasi"],
    "Indonesia": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Palembang", "Depok", "Tangerang", "Bekasi", "Padang", "Denpasar", "Malang", "Bogor", "Batam", "Pekanbaru", "Bandar Lampung", "Yogyakarta", "Manado", "Balikpapan"],
    "Iran": ["Tehran", "Mashhad", "Isfahan", "Karaj", "Shiraz", "Tabriz", "Qom", "Ahvaz", "Kermanshah", "Urmia", "Rasht", "Zahedan", "Hamadan", "Kerman", "Yazd", "Ardabil", "Bandar Abbas", "Arak", "Eslamshahr", "Zanjan"],
    "Iraq": ["Baghdad", "Basra", "Mosul", "Erbil", "Najaf", "Karbala", "Nasiriyah", "Kirkuk", "Sulaymaniyah", "Amarah", "Diwaniyah", "Ramadi", "Samawah", "Fallujah", "Duhok", "Baqubah", "Kut", "Hillah", "Samarra", "Tikrit"],
    "Ireland": ["Dublin", "Cork", "Limerick", "Galway", "Waterford", "Drogheda", "Dundalk", "Swords", "Bray", "Navan", "Kilkenny", "Ennis", "Carlow", "Tralee", "Newbridge", "Naas", "Athlone", "Portlaoise", "Mullingar", "Wexford"],
    "Israel": ["Jerusalem", "Tel Aviv", "Haifa", "Rishon LeZion", "Petah Tikva", "Ashdod", "Netanya", "Beersheba", "Bnei Brak", "Holon", "Ramat Gan", "Rehovot", "Bat Yam", "Ashkelon", "Herzliya", "Kfar Saba", "Modi'in", "Nazareth", "Lod", "Ramla"],
    "Italy": ["Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna", "Florence", "Bari", "Catania", "Venice", "Verona", "Messina", "Padua", "Trieste", "Brescia", "Parma", "Taranto", "Prato", "Modena"],
    "Ivory Coast": ["Abidjan", "Bouake", "Daloa", "Yamoussoukro", "San-Pedro", "Korhogo", "Man", "Divo", "Gagnoa", "Anyama", "Abengourou", "Agboville", "Grand-Bassam", "Dabou", "Bondoukou", "Soubre", "Sinfra", "Issia", "Ferkessedougou", "Odienne"],
    "Jamaica": ["Kingston", "Spanish Town", "Montego Bay", "Portmore", "May Pen", "Mandeville", "Old Harbour", "Savanna-la-Mar", "Port Antonio", "Linstead", "Half Way Tree", "Ocho Rios", "Falmouth", "Bog Walk", "Morant Bay", "Negril", "Santa Cruz", "Christiana", "Black River", "Lucea"],
    "Japan": ["Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo", "Fukuoka", "Kobe", "Kyoto", "Kawasaki", "Saitama", "Hiroshima", "Sendai", "Kitakyushu", "Chiba", "Sakai", "Niigata", "Hamamatsu", "Kumamoto", "Okayama", "Shizuoka"],
    "Jordan": ["Amman", "Zarqa", "Irbid", "Russeifa", "Aqaba", "Salt", "Mafraq", "Jerash", "Madaba", "Karak", "Tafilah", "Ma'an", "Ramtha", "Sahab", "Fuheis", "Ajloun", "Dhiban", "Baqa'a", "Wadi Musa", "Suwaylih"],
    "Kazakhstan": ["Almaty", "Astana", "Shymkent", "Karaganda", "Aktobe", "Taraz", "Pavlodar", "Ust-Kamenogorsk", "Semey", "Atyrau", "Kostanay", "Kyzylorda", "Uralsk", "Petropavl", "Aktau", "Temirtau", "Turkestan", "Kokshetau", "Taldykorgan", "Ekibastuz"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Malindi", "Kitale", "Garissa", "Kakamega", "Nyeri", "Machakos", "Meru", "Naivasha", "Kericho", "Embu", "Migori", "Bungoma", "Kisii", "Lamu"],
    "Kiribati": ["South Tarawa", "Betio", "Bikenibeu", "Bairiki", "Teaoraereke", "Eita", "Abaokoro", "Buota", "Temaiku", "Antebuka", "Tabiteuea", "Abemama", "Marakei", "Butaritari", "Kuria", "Aranuka", "Nonouti", "Onotoa", "Beru", "Tabuaeran"],
    "Kuwait": ["Kuwait City", "Al Ahmadi", "Hawalli", "As Salimiyah", "Sabah as Salim", "Al Farwaniyah", "Al Fahahil", "Jahra", "Ar Riqqah", "Mubarak al-Kabeer", "Al Fintas", "Salwa", "Abu Halifa", "Al Jahra", "Kaifan", "Al Rai", "Bayan", "Fahaheel", "Sabhan", "Mangaf"],
    "Kyrgyzstan": ["Bishkek", "Osh", "Jalal-Abad", "Karakol", "Tokmok", "Kara-Balta", "Uzgen", "Balykchy", "Naryn", "Talas", "Kant", "Cholpon-Ata", "Kyzyl-Kiya", "Isfana", "Batken", "Kara-Suu", "Kok-Jangak", "Nookat", "Toktogul", "Suzak"],
    "Laos": ["Vientiane", "Pakse", "Savannakhet", "Luang Prabang", "Thakhek", "Xam Neua", "Phonsavan", "Vang Vieng", "Muang Xay", "Attapeu", "Luang Namtha", "Saravan", "Muang Xay", "Ban Houayxay", "Xaignabouli", "Phongsaly", "Muang Khammouan", "Champasak", "Vientiane", "Muang Vangviang"],
    "Latvia": ["Riga", "Daugavpils", "Liepaja", "Jelgava", "Jurmala", "Ventspils", "Rezekne", "Valmiera", "Jekabpils", "Ogre", "Tukums", "Cesis", "Salaspils", "Kuldiga", "Saldus", "Talsi", "Dobele", "Krasi", "Bauska", "Sigulda"],
    "Lebanon": ["Beirut", "Tripoli", "Sidon", "Tyre", "Zahle", "Baalbek", "Jounieh", "Byblos", "Nabatieh", "Batroun", "Aley", "Bhamdoun", "Zgharta", "Rachaya", "Marjayoun", "Bint Jbeil", "Hasbaya", "Chtaura", "Broummana", "Antelias"],
    "Lesotho": ["Maseru", "Teyateyaneng", "Mafeteng", "Hlotse", "Mohale's Hoek", "Maputsoe", "Qacha's Nek", "Quthing", "Butha-Buthe", "Thaba-Tseka", "Mokhotlong", "Roma", "Semonkong", "Peka", "Nazareth", "Marakabei", "Mapoteng", "Malealea", "Morija", "Hlotse"],
    "Liberia": ["Monrovia", "Gbarnga", "Kakata", "Bensonville", "Harper", "Voinjama", "Buchanan", "Zwedru", "New Kru Town", "Ganta", "Robertsport", "Sanniquellie", "Fish Town", "Barclayville", "Greenville", "Bopolu", "Cestos City", "Tubmanburg", "Foya", "Kle"],
    "Libya": ["Tripoli", "Benghazi", "Misrata", "Bayda", "Zawiya", "Zliten", "Ajdabiya", "Tobruk", "Sabha", "Sirte", "Derna", "Khoms", "Zuwara", "Gharyan", "Sabratha", "Bani Walid", "Marj", "Nalut", "Murzuq", "Yafran"],
    "Liechtenstein": ["Vaduz", "Schaan", "Triesen", "Balzers", "Eschen", "Mauren", "Triesenberg", "Ruggell", "Gamprin", "Schellenberg", "Planken", "Nendeln", "Bendern", "Malbun", "Masescha", "Rotenboden", "Steg", "Vaduz Oberland", "Sax", "Rotenwiese"],
    "Lithuania": ["Vilnius", "Kaunas", "Klaipeda", "Siauliai", "Panevezys", "Alytus", "Marijampole", "Mazeikiai", "Jonava", "Utena", "Kedainiai", "Telsiai", "Taurage", "Ukmerge", "Visaginas", "Plunge", "Kretinga", "Silute", "Palanga", "Radviliskis"],
    "Luxembourg": ["Luxembourg City", "Esch-sur-Alzette", "Differdange", "Dudelange", "Ettelbruck", "Diekirch", "Wiltz", "Echternach", "Rumelange", "Bettembourg", "Grevenmacher", "Remich", "Mersch", "Vianden", "Clervaux", "Bascharage", "Steinfort", "Junglinster", "Redange", "Kayl"],
    "Madagascar": ["Antananarivo", "Toamasina", "Antsirabe", "Mahajanga", "Fianarantsoa", "Toliara", "Antsiranana", "Ambovombe", "Farafangana", "Mananjary", "Ambatondrazaka", "Manakara", "Moramanga", "Fenoarivo", "Morondava", "Sambava", "Ihosy", "Tsiroanomandidy", "Nosy Be", "Maevatanana"],
    "Malawi": ["Lilongwe", "Blantyre", "Mzuzu", "Zomba", "Kasungu", "Mangochi", "Karonga", "Salima", "Nkhotakota", "Liwonde", "Balaka", "Dedza", "Mchinji", "Rumphi", "Mzimba", "Nsanje", "Ntcheu", "Chitipa", "Mwanza", "Neno"],
    "Malaysia": ["Kuala Lumpur", "George Town", "Ipoh", "Johor Bahru", "Shah Alam", "Petaling Jaya", "Klang", "Malacca City", "Kota Kinabalu", "Kuching", "Kuantan", "Seremban", "Alor Setar", "Sungai Petani", "Miri", "Sandakan", "Taiping", "Sibu", "Bintulu", "Kuala Terengganu"],
    "Maldives": ["Male", "Addu City", "Fuvahmulah", "Kulhudhuffushi", "Thinadhoo", "Naifaru", "Eydhafushi", "Hithadhoo", "Dhidhdhoo", "Mahibadhoo", "Ungoofaaru", "Muli", "Veymandoo", "Guraidhoo", "Rasdhoo", "Manadhoo", "Feydhoo", "Funadhoo", "Kudahuvadhoo", "Fonadhoo"],
    "Mali": ["Bamako", "Sikasso", "Mopti", "Koutiala", "Segou", "Kayes", "Gao", "Timbuktu", "Kati", "Kolokani", "San", "Bougouni", "Nioro du Sahel", "Bafoulabe", "Djenne", "Douentza", "Kidal", "Nara", "Ansongo", "Yorosso"],
    "Malta": ["Valletta", "Birkirkara", "Mosta", "Qormi", "Zabbar", "St. Paul's Bay", "Sliema", "Zejtun", "Naxxar", "San Gwann", "Fgura", "Zabbar", "Marsaskala", "Rabat", "Paola", "Attard", "Luqa", "Gzira", "Hamrun", "Marsa"],
    "Marshall Islands": ["Majuro", "Ebeye", "Arno", "Jaluit", "Wotje", "Ailinglaplap", "Namdrik", "Mili", "Kwajalein", "Rongelap", "Utrik", "Enewetak", "Likiep", "Maloelap", "Namu", "Ailuk", "Ujae", "Lae", "Bikini", "Rongrik"],
    "Mauritania": ["Nouakchott", "Nouadhibou", "Kiffa", "Kaedi", "Rosso", "Zouerate", "Atar", "Selibaby", "Akjoujt", "Aleg", "Nema", "Boutilimit", "Tidjikja", "Aioun", "Chinguetti", "Boghe", "Timbedgha", "Kankossa", "Rachid", "Bir Moghrein"],
    "Mauritius": ["Port Louis", "Beau Bassin-Rose Hill", "Vacoas-Phoenix", "Curepipe", "Quatre Bornes", "Triolet", "Goodlands", "Centre de Flacq", "Bel Air Riviere Seche", "Mahebourg", "Saint Pierre", "Rose Belle", "Grand Baie", "Flic en Flac", "Chemin Grenier", "Souillac", "Cluny", "Riviere du Rempart", "Pamplemousses", "Grand Gaube"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "Leon", "Juarez", "Zapopan", "Merida", "San Luis Potosi", "Aguascalientes", "Hermosillo", "Saltillo", "Mexicali", "Culiacan", "Queretaro", "Chihuahua", "Morelia", "Cancun", "Acapulco"],
    "Micronesia": ["Palikir", "Weno", "Kolonia", "Tofol", "Colonia", "Nett", "Kitti", "Madolenihmw", "Sokehs", "U", "Faichuk", "Fefan", "Tol", "Udot", "Fananu", "Nomwin", "Pisar", "Pingelap", "Mokil", "Losap"],
    "Moldova": ["Chisinau", "Balti", "Tiraspol", "Bender", "Cahul", "Ungheni", "Soroca", "Orhei", "Comrat", "Edinet", "Ceadir-Lunga", "Straseni", "Causeni", "Drochia", "Basarabeasca", "Hincesti", "Falesti", "Anenii Noi", "Nisporeni", "Rezina"],
    "Monaco": ["Monaco-Ville", "Monte Carlo", "La Condamine", "Fontvieille", "Larvotto", "Moneghetti", "Saint Roman", "La Rousse", "Les Revoires", "Jardin Exotique", "Le Portier", "Ravin de Sainte Devote", "Saint Michel", "La Colle", "Vallon Sainte Devote", "Cap d'Ail border", "Moulins", "Spelugues", "Port Hercule", "Rocher"],
    "Mongolia": ["Ulaanbaatar", "Erdenet", "Darkhan", "Choibalsan", "Mörön", "Nalaikh", "Khovd", "Ölgii", "Bayankhongor", "Arvaikheer", "Baruun-Urt", "Sükhbaatar", "Uliastai", "Zuunmod", "Mandalgovi", "Choir", "Altai", "Tsetserleg", "Ulaangom", "Dalanzadgad"],
    "Montenegro": ["Podgorica", "Niksic", "Herceg Novi", "Pljevlja", "Bar", "Bijelo Polje", "Cetinje", "Budva", "Berane", "Ulcinj", "Tivat", "Rozaje", "Danilovgrad", "Kotor", "Mojkovac", "Kolasin", "Zabljak", "Andrijevica", "Petnjica", "Gusinje"],
    "Morocco": ["Casablanca", "Rabat", "Fez", "Marrakesh", "Tangier", "Agadir", "Meknes", "Oujda", "Kenitra", "Tetouan", "Safi", "El Jadida", "Nador", "Beni Mellal", "Khouribga", "Taza", "Essaouira", "Larache", "Khemisset", "Settat"],
    "Mozambique": ["Maputo", "Matola", "Beira", "Nampula", "Chimoio", "Nacala", "Quelimane", "Tete", "Xai-Xai", "Lichinga", "Pemba", "Inhambane", "Cuamba", "Angoche", "Dondo", "Chibuto", "Maxixe", "Montepuez", "Chokwe", "Mocuba"],
    "Myanmar": ["Yangon", "Mandalay", "Naypyidaw", "Mawlamyine", "Bago", "Pathein", "Monywa", "Meiktila", "Myitkyina", "Taunggyi", "Sittwe", "Pyay", "Dawei", "Hpa-An", "Myeik", "Lashio", "Magway", "Loikaw", "Hakha", "Kalay"],
    "Namibia": ["Windhoek", "Rundu", "Walvis Bay", "Oshakati", "Swakopmund", "Katima Mulilo", "Grootfontein", "Rehoboth", "Otjiwarongo", "Okahandja", "Ongwediva", "Ondangwa", "Tsumeb", "Gobabis", "Keetmanshoop", "Mariental", "Karibib", "Outjo", "Usakos", "Luderitz"],
    "Nauru": ["Yaren", "Denigomodu", "Aiwo", "Baiti", "Anabar", "Anetan", "Anibare", "Boe", "Buada", "Ewa", "Ijuw", "Meneng", "Nibok", "Uaboe", "Yaren District", "Location", "Menen", "Nauru Central", "Bomii", "Iruwa"],
    "Nepal": ["Kathmandu", "Pokhara", "Lalitpur", "Bharatpur", "Biratnagar", "Birgunj", "Dharan", "Butwal", "Hetauda", "Janakpur", "Nepalgunj", "Dhangadhi", "Itahari", "Tulsipur", "Ghorahi", "Bhaktapur", "Damak", "Gorkha", "Ilam", "Baglung"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Tilburg", "Groningen", "Almere", "Breda", "Nijmegen", "Enschede", "Haarlem", "Arnhem", "Zaanstad", "Amersfoort", "Apeldoorn", "Den Bosch", "Hoofddorp", "Maastricht", "Leiden"],
    "New Zealand": ["Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga", "Napier-Hastings", "Dunedin", "Palmerston North", "Nelson", "Rotorua", "New Plymouth", "Whangarei", "Invercargill", "Whanganui", "Gisborne", "Timaru", "Queenstown", "Blenheim", "Pukekohe", "Taupo"],
    "Nicaragua": ["Managua", "Leon", "Masaya", "Chinandega", "Matagalpa", "Esteli", "Granada", "Ciudad Sandino", "Tipitapa", "Jinotega", "Juigalpa", "El Viejo", "Nueva Guinea", "Diriamba", "Ocotal", "Chichigalpa", "Bluefields", "San Marcos", "Jinotepe", "Boaco"],
    "Niger": ["Niamey", "Zinder", "Maradi", "Agadez", "Tahoua", "Dosso", "Diffa", "Tillaberi", "Arlit", "Birni-N'Konni", "Gaya", "Tessaoua", "Madaoua", "Mirriah", "Matameye", "Dogondoutchi", "Illela", "Tera", "Say", "Goure"],
    "Nigeria": ["Lagos", "Kano", "Ibadan", "Abuja", "Port Harcourt", "Benin City", "Kaduna", "Maiduguri", "Zaria", "Aba", "Jos", "Ilorin", "Oyo", "Enugu", "Abeokuta", "Sokoto", "Onitsha", "Warri", "Calabar", "Uyo"],
    "North Korea": ["Pyongyang", "Hamhung", "Chongjin", "Nampo", "Wonsan", "Sinuiju", "Kaesong", "Sariwon", "Hyesan", "Kanggye", "Haeju", "Kimchaek", "Anju", "Manpo", "Rason", "Pyongsong", "Songnim", "Tanchon", "Sinpo", "Chongjin"],
    "North Macedonia": ["Skopje", "Bitola", "Kumanovo", "Prilep", "Tetovo", "Veles", "Stip", "Ohrid", "Gostivar", "Strumica", "Kavadarci", "Kocani", "Kicevo", "Struga", "Radovis", "Gevgelija", "Debar", "Kriva Palanka", "Sveti Nikole", "Negotino"],
    "Norway": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Baerum", "Kristiansand", "Fredrikstad", "Tromso", "Drammen", "Sandnes", "Sarpsborg", "Skien", "Alesund", "Sandefjord", "Haugesund", "Tonsberg", "Moss", "Porsgrunn", "Bodo", "Arendal"],
    "Oman": ["Muscat", "Seeb", "Salalah", "Bawshar", "Sohar", "As Suwayq", "Ibri", "Saham", "Barka", "Rustaq", "Nizwa", "Sur", "Buraimi", "Khasab", "Ibra", "Yanqul", "Adam", "Duqm", "Shinas", "Al Mudhaibi"],
    "Pakistan": ["Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Multan", "Peshawar", "Islamabad", "Quetta", "Sialkot", "Gujranwala", "Hyderabad", "Bahawalpur", "Sargodha", "Sukkur", "Larkana", "Sheikhupura", "Rahim Yar Khan", "Jhang", "Gujrat", "Mardan"],
    "Palau": ["Ngerulmud", "Koror", "Airai", "Meyuns", "Kloulklubed", "Ngiwal", "Ngardmau", "Ngeremlengui", "Melekeok", "Ngchesar", "Aimeliik", "Angaur", "Sonsorol", "Hatohobei", "Peleliu", "Ngatpang", "Ngarchelong", "Kayangel", "Ollei", "Ngerechelong"],
    "Palestine": ["Gaza City", "Ramallah", "Hebron", "Nablus", "Bethlehem", "Khan Yunis", "Jenin", "Rafah", "Tulkarm", "Qalqilya", "Jericho", "Tubas", "Deir al-Balah", "Beit Lahia", "Beit Hanoun", "Salfit", "Halhul", "Yatta", "Dura", "Beitunia"],
    "Panama": ["Panama City", "San Miguelito", "Tocumen", "David", "Arraijan", "Colon", "La Chorrera", "Pacora", "Santiago", "Chitre", "Penonome", "Las Cumbres", "Chilibre", "Aguadulce", "Puerto Armuelles", "Changuinola", "La Concepcion", "Las Tablas", "Boquete", "Bocas del Toro"],
    "Papua New Guinea": ["Port Moresby", "Lae", "Mount Hagen", "Madang", "Wewak", "Goroka", "Kokopo", "Kimbe", "Mendi", "Kavieng", "Alotau", "Popondetta", "Vanimo", "Daru", "Kundiawa", "Bulolo", "Kerema", "Wabag", "Manus", "Buka"],
    "Paraguay": ["Asuncion", "Ciudad del Este", "San Lorenzo", "Luque", "Capiata", "Lambare", "Fernando de la Mora", "Limpio", "Nemby", "Encarnacion", "Mariano Roque Alonso", "Pedro Juan Caballero", "Villa Elisa", "Coronel Oviedo", "Itaugua", "Caaguazu", "Concepcion", "Villarrica", "Presidente Franco", "San Antonio"],
    "Peru": ["Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura", "Iquitos", "Cusco", "Chimbote", "Huancayo", "Tacna", "Ica", "Juliaca", "Sullana", "Ayacucho", "Cajamarca", "Pucallpa", "Chincha Alta", "Huanuco", "Puno", "Tarapoto"],
    "Philippines": ["Manila", "Quezon City", "Davao City", "Caloocan", "Cebu City", "Zamboanga City", "Taguig", "Antipolo", "Pasig", "Cagayan de Oro", "Paranaque", "Valenzuela", "Dasmarinas", "General Santos", "Bacolod", "Iloilo City", "Las Pinas", "Makati", "Marikina", "Baguio"],
    "Poland": ["Warsaw", "Krakow", "Lodz", "Wroclaw", "Poznan", "Gdansk", "Szczecin", "Bydgoszcz", "Lublin", "Bialystok", "Katowice", "Gdynia", "Czestochowa", "Radom", "Sosnowiec", "Torun", "Kielce", "Gliwice", "Zabrze", "Bytom"],
    "Portugal": ["Lisbon", "Porto", "Vila Nova de Gaia", "Amadora", "Braga", "Coimbra", "Setubal", "Almada", "Agualva-Cacem", "Queluz", "Funchal", "Rio Tinto", "Evora", "Aveiro", "Faro", "Viseu", "Guimaraes", "Leiria", "Odivelas", "Barreiro"],
    "Qatar": ["Doha", "Al Rayyan", "Umm Salal", "Al Wakrah", "Al Khor", "Dukhan", "Mesaieed", "Lusail", "Al Shamal", "Al Daayen", "Al Ghuwariyah", "Al Jumaliyah", "Simaisma", "Ras Laffan", "Fuwayrit", "Al Kharaitiyat", "Abu Samra", "Al Mashaf", "Al Ruwais", "Dukhan City"],
    "Romania": ["Bucharest", "Cluj-Napoca", "Timisoara", "Iasi", "Constanta", "Craiova", "Brasov", "Galati", "Ploiesti", "Oradea", "Braila", "Arad", "Pitesti", "Sibiu", "Bacau", "Targu Mures", "Baia Mare", "Buzau", "Botosani", "Satu Mare"],
    "Russia": ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod", "Chelyabinsk", "Samara", "Omsk", "Rostov-on-Don", "Ufa", "Krasnoyarsk", "Voronezh", "Perm", "Volgograd", "Krasnodar", "Saratov", "Tyumen", "Tolyatti", "Izhevsk"],
    "Rwanda": ["Kigali", "Butare", "Gitarama", "Ruhengeri", "Gisenyi", "Byumba", "Cyangugu", "Kibungo", "Kibuye", "Nyanza", "Rwamagana", "Muhanga", "Musanze", "Rubavu", "Nyagatare", "Karongi", "Huye", "Rusizi", "Kayonza", "Gicumbi"],
    "Saint Kitts and Nevis": ["Basseterre", "Charlestown", "Sandy Point Town", "Cayon", "Dieppe Bay Town", "Saint Paul's", "Tabernacle", "Middle Island", "Gingerland", "Newcastle", "Old Road Town", "Nicola Town", "Half Way Tree", "Fig Tree", "Mansion", "Molineux", "Trinity", "Monkey Hill", "Cotton Ground", "Rawlins"],
    "Saint Lucia": ["Castries", "Vieux Fort", "Micoud", "Soufriere", "Dennery", "Gros Islet", "Laborie", "Choiseul", "Anse la Raye", "Canaries", "Babonneau", "Praslin", "Forest Hill", "Marigot", "Ciceron", "Grande Riviere", "Bexon", "Cul de Sac", "Monchy", "Fond Assau"],
    "Saint Vincent and the Grenadines": ["Kingstown", "Georgetown", "Barrouallie", "Port Elizabeth", "Chateaubelair", "Layou", "Biabou", "Calliaqua", "Kingstown Park", "Fancy", "Mesopotamia", "Byera", "Colonarie", "Stubbs", "Questelles", "Rose Hall", "Sandy Bay", "Union Island", "Bequia", "Canouan"],
    "Samoa": ["Apia", "Asau", "Mulifanua", "Faleula", "Vaitele", "Siusega", "Salelologa", "Lalomanu", "Falealupo", "Safotu", "Leulumoega", "Fasito'outa", "Solosolo", "Lano", "Saleimoa", "Fagamalo", "Manase", "Vaiala", "Nofoalii", "Malie"],
    "San Marino": ["City of San Marino", "Serravalle", "Borgo Maggiore", "Domagnano", "Fiorentino", "Acquaviva", "Faetano", "Chiesanuova", "Montegiardino", "Dogana", "Falciano", "Murata", "Ca' Rigo", "Torraccia", "San Giovanni", "Cailungo", "Fiorina", "Valdragone", "Poggio Casalino", "Galazzano"],
    "Sao Tome and Principe": ["Sao Tome", "Santo Antonio", "Neves", "Santana", "Trindade", "Guadalupe", "Santa Cruz", "Angolares", "Sao Joao dos Angolares", "Porto Alegre", "Ribeira Afonso", "Pantufo", "Madalena", "Agua Grande", "Micoló", "Ribeira Peixe", "Boa Morte", "Almas", "Neves 2", "Bombom"],
    "Saudi Arabia": ["Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Khobar", "Taif", "Tabuk", "Buraidah", "Khamis Mushait", "Hail", "Najran", "Jubail", "Abha", "Yanbu", "Al Kharj", "Qatif", "Al Hofuf", "Arar", "Sakaka"],
    "Senegal": ["Dakar", "Touba", "Thies", "Rufisque", "Kaolack", "Mbour", "Ziguinchor", "Saint-Louis", "Diourbel", "Louga", "Tambacounda", "Kolda", "Richard Toll", "Kaffrine", "Fatick", "Mbacke", "Guediawaye", "Pikine", "Bignona", "Joal-Fadiouth"],
    "Serbia": ["Belgrade", "Novi Sad", "Nis", "Kragujevac", "Subotica", "Zrenjanin", "Pancevo", "Cacak", "Novi Pazar", "Kraljevo", "Smederevo", "Leskovac", "Uzice", "Vranje", "Sabac", "Sombor", "Pozarevac", "Pirot", "Zajecar", "Kikinda"],
    "Seychelles": ["Victoria", "Anse Boileau", "Beau Vallon", "Anse Royale", "Takamaka", "Bel Ombre", "Cascade", "Glacis", "Grand Anse", "Baie Lazare", "Anse Etoile", "Port Glaud", "Roche Caiman", "La Digue", "Praslin", "Anse aux Pins", "Plaisance", "Mont Fleuri", "Pointe Larue", "English River"],
    "Sierra Leone": ["Freetown", "Bo", "Kenema", "Koidu", "Makeni", "Lunsar", "Port Loko", "Kabala", "Magburaka", "Waterloo", "Kailahun", "Pujehun", "Bonthe", "Moyamba", "Kambia", "Segbwema", "Yengema", "Mattru Jong", "Rokupr", "Kayima"],
    "Singapore": ["Singapore", "Jurong West", "Woodlands", "Tampines", "Sengkang", "Yishun", "Hougang", "Bedok", "Ang Mo Kio", "Bukit Batok", "Punggol", "Bukit Merah", "Choa Chu Kang", "Toa Payoh", "Pasir Ris", "Bishan", "Serangoon", "Clementi", "Bukit Panjang", "Queenstown"],
    "Slovakia": ["Bratislava", "Kosice", "Presov", "Zilina", "Banska Bystrica", "Nitra", "Trnava", "Martin", "Trencin", "Poprad", "Prievidza", "Zvolen", "Povazska Bystrica", "Michalovce", "Spisska Nova Ves", "Komarno", "Levice", "Humenne", "Bardejov", "Liptovsky Mikulas"],
    "Slovenia": ["Ljubljana", "Maribor", "Celje", "Kranj", "Velenje", "Koper", "Novo Mesto", "Ptuj", "Trbovlje", "Kamnik", "Nova Gorica", "Domzale", "Skofja Loka", "Murska Sobota", "Jesenice", "Izola", "Slovenj Gradec", "Postojna", "Bled", "Piran"],
    "Solomon Islands": ["Honiara", "Auki", "Gizo", "Buala", "Kirakira", "Lata", "Tulagi", "Taro", "Munda", "Malango", "Noro", "Tigoa", "Choiseul Bay", "Afutara", "Sasamungga", "Buma", "Batuna", "Fasi", "Ringgi", "Yandina"],
    "Somalia": ["Mogadishu", "Hargeisa", "Kismayo", "Baidoa", "Bosaso", "Berbera", "Galkayo", "Merca", "Jowhar", "Beledweyne", "Burao", "Garowe", "Erigavo", "Las Anod", "Qardho", "Baki", "Zeila", "Buurhakaba", "Wanlaweyn", "Afgooye"],
    "South Africa": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth", "Bloemfontein", "Nelspruit", "Kimberley", "Polokwane", "Rustenburg", "East London", "Pietermaritzburg", "Vereeniging", "Welkom", "Newcastle", "George", "Witbank", "Klerksdorp", "Springs", "Krugersdorp"],
    "South Korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Suwon", "Ulsan", "Changwon", "Goyang", "Yongin", "Seongnam", "Bucheon", "Cheongju", "Ansan", "Jeonju", "Anyang", "Cheonan", "Namyangju", "Pohang"],
    "South Sudan": ["Juba", "Wau", "Malakal", "Yei", "Aweil", "Bor", "Rumbek", "Yambio", "Torit", "Bentiu", "Kuajok", "Nimule", "Maridi", "Renk", "Nasir", "Akobo", "Terekeka", "Kapoeta", "Yirol", "Raga"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Malaga", "Murcia", "Palma", "Las Palmas", "Bilbao", "Alicante", "Cordoba", "Valladolid", "Vigo", "Gijon", "Granada", "A Coruna", "Vitoria-Gasteiz", "Elche", "Oviedo"],
    "Sri Lanka": ["Colombo", "Kandy", "Galle", "Jaffna", "Negombo", "Kurunegala", "Anuradhapura", "Trincomalee", "Batticaloa", "Matara", "Ratnapura", "Badulla", "Puttalam", "Chilaw", "Nuwara Eliya", "Kalutara", "Gampaha", "Ampara", "Vavuniya", "Polonnaruwa"],
    "Sudan": ["Khartoum", "Omdurman", "Nyala", "Port Sudan", "Kassala", "El Obeid", "Gedaref", "Wad Madani", "El Fasher", "Kosti", "Atbara", "Dongola", "Sennar", "Zalingei", "El Geneina", "Rabak", "Damazin", "Nahr el Nil", "Shendi", "Singa"],
    "Suriname": ["Paramaribo", "Lelydorp", "Nieuw Nickerie", "Moengo", "Nieuw Amsterdam", "Mariënburg", "Wageningen", "Albina", "Groningen", "Brokopondo", "Totness", "Onverwacht", "Cottica", "Meerzorg", "Domburg", "Brownsweg", "Apoera", "Bitagron", "Klaaskreek", "Pokigron"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmo", "Uppsala", "Vasteras", "Orebro", "Linkoping", "Helsingborg", "Jonkoping", "Norrkoping", "Lund", "Umea", "Gavle", "Boras", "Sodertalje", "Eskilstuna", "Halmstad", "Vaxjo", "Karlstad", "Sundsvall"],
    "Switzerland": ["Zurich", "Geneva", "Basel", "Lausanne", "Bern", "Winterthur", "Lucerne", "St. Gallen", "Lugano", "Biel", "Thun", "Kriens", "La Chaux-de-Fonds", "Fribourg", "Schaffhausen", "Vernier", "Chur", "Neuchatel", "Uster", "Sion"],
    "Syria": ["Damascus", "Aleppo", "Homs", "Latakia", "Hama", "Deir ez-Zor", "Raqqa", "Daraa", "Al-Hasakah", "Idlib", "Qamishli", "Tartus", "Douma", "Manbij", "Al-Bab", "Jableh", "As-Suwayda", "Tal Abyad", "Salamiyah", "Palmyra"],
    "Taiwan": ["Taipei", "Kaohsiung", "Taichung", "Tainan", "New Taipei", "Taoyuan", "Hsinchu", "Keelung", "Chiayi", "Changhua", "Pingtung", "Yunlin", "Nantou", "Yilan", "Hualien", "Taitung", "Miaoli", "Douliu", "Zhubei", "Puzi"],
    "Tajikistan": ["Dushanbe", "Khujand", "Kulob", "Bokhtar", "Istaravshan", "Konibodom", "Tursunzoda", "Panjakent", "Isfara", "Vahdat", "Norak", "Khorog", "Kanibadam", "Farkhor", "Rogun", "Kolkhozobod", "Yovon", "Danghara", "Hisor", "Shahrinav"],
    "Tanzania": ["Dar es Salaam", "Dodoma", "Mwanza", "Arusha", "Mbeya", "Morogoro", "Tanga", "Kigoma", "Zanzibar City", "Moshi", "Iringa", "Songea", "Musoma", "Shinyanga", "Bukoba", "Sumbawanga", "Kahama", "Singida", "Lindi", "Njombe"],
    "Thailand": ["Bangkok", "Nonthaburi", "Nakhon Ratchasima", "Chiang Mai", "Hat Yai", "Udon Thani", "Pak Kret", "Khon Kaen", "Chonburi", "Rayong", "Nakhon Si Thammarat", "Ubon Ratchathani", "Surat Thani", "Nakhon Pathom", "Phuket", "Pattaya", "Lampang", "Songkhla", "Chiang Rai", "Trang"],
    "Timor-Leste": ["Dili", "Baucau", "Maliana", "Suai", "Same", "Aileu", "Ainaro", "Los Palos", "Liquica", "Manatuto", "Viqueque", "Gleno", "Pante Macassar", "Ermera", "Lospalos", "Atambua border", "Baguia", "Venilale", "Laga", "Ainaro Town"],
    "Togo": ["Lome", "Sokode", "Kara", "Kpalime", "Atakpame", "Dapaong", "Tsevie", "Aneho", "Mango", "Bassar", "Tabligbo", "Sansanne-Mango", "Notse", "Vogan", "Badou", "Amlame", "Sotouboua", "Tchamba", "Kande", "Blitta"],
    "Tonga": ["Nuku'alofa", "Neiafu", "Haveluloto", "Vaini", "Pangai", "Ohonua", "Tofoa", "Longoteme", "Kolonga", "Havelu", "Nuku'alofa Outer", "Hihifo", "Kolovai", "Houma", "Fua'amotu", "Kanokupolu", "Ha'alalo", "Fatai", "Vaotu'u", "Falehau"],
    "Trinidad and Tobago": ["Port of Spain", "San Fernando", "Chaguanas", "Arima", "Point Fortin", "Scarborough", "Sangre Grande", "Couva", "Princes Town", "Rio Claro", "Siparia", "Tunapuna", "Diego Martin", "Marabella", "Penal", "Debe", "Fyzabad", "Cunupia", "Claxton Bay", "Plymouth"],
    "Tunisia": ["Tunis", "Sfax", "Sousse", "Kairouan", "Bizerte", "Gabes", "Ariana", "Gafsa", "Monastir", "Ben Arous", "Kasserine", "Medenine", "Nabeul", "Tataouine", "Beja", "Jendouba", "Mahdia", "Sidi Bouzid", "Zarzis", "Hammamet"],
    "Turkey": ["Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Gaziantep", "Konya", "Antalya", "Kayseri", "Mersin", "Diyarbakir", "Eskisehir", "Samsun", "Denizli", "Sanliurfa", "Malatya", "Erzurum", "Van", "Batman", "Trabzon"],
    "Turkmenistan": ["Ashgabat", "Turkmenabat", "Dashoguz", "Mary", "Balkanabat", "Bayramaly", "Tejen", "Serdar", "Turkmenbashi", "Kaka", "Gazojak", "Abadan", "Bereket", "Gyzylarbat", "Yolotan", "Serakhs", "Kerki", "Farap", "Bakharden", "Atamurat"],
    "Tuvalu": ["Funafuti", "Vaiaku", "Alapi", "Fongafale", "Amatuku", "Nanumea", "Nanumaga", "Niutao", "Nui", "Vaitupu", "Nukufetau", "Nukulaelae", "Niulakita", "Asau", "Motufoua", "Teone", "Tanrake", "Lolua", "Savave", "Kulia"],
    "Uganda": ["Kampala", "Nansana", "Kira", "Ssabagabo", "Mbarara", "Mukono", "Njeru", "Gulu", "Lira", "Mbale", "Jinja", "Kasese", "Masaka", "Entebbe", "Hoima", "Arua", "Fort Portal", "Soroti", "Iganga", "Kabale"],
    "Ukraine": ["Kyiv", "Kharkiv", "Odesa", "Dnipro", "Donetsk", "Zaporizhzhia", "Lviv", "Kryvyi Rih", "Mykolaiv", "Mariupol", "Luhansk", "Vinnytsia", "Makiivka", "Sevastopol", "Simferopol", "Kherson", "Poltava", "Chernihiv", "Cherkasy", "Sumy"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain", "Khor Fakkan", "Kalba", "Dibba Al-Fujairah", "Madinat Zayed", "Ruwais", "Liwa Oasis", "Jebel Ali", "Dhaid", "Masafi", "Hatta", "Ghayathi", "Sila"],
    "United Kingdom": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", "Leeds", "Sheffield", "Edinburgh", "Bristol", "Cardiff", "Leicester", "Coventry", "Belfast", "Nottingham", "Newcastle", "Southampton", "Bradford", "Stoke-on-Trent", "Wolverhampton", "Plymouth"],
    "United States": ["New York City", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin", "San Jose", "Jacksonville", "San Francisco", "Columbus", "Charlotte", "Indianapolis", "Seattle", "Denver", "Boston", "Nashville","Florida","California"],
    "Uruguay": ["Montevideo", "Salto", "Ciudad de la Costa", "Paysandu", "Las Piedras", "Rivera", "Maldonado", "Tacuarembo", "Melo", "Mercedes", "Artigas", "Minas", "San Jose de Mayo", "Durazno", "Florida", "Barros Blancos", "Colonia del Sacramento", "Treinta y Tres", "Rocha", "Fray Bentos"],
    "Uzbekistan": ["Tashkent", "Namangan", "Samarkand", "Andijan", "Nukus", "Bukhara", "Qarshi", "Fergana", "Jizzakh", "Kokand", "Margilan", "Chirchiq", "Termez", "Urgench", "Angren", "Navoiy", "Gulistan", "Olmaliq", "Bekabad", "Denov"],
    "Vanuatu": ["Port Vila", "Luganville", "Norsup", "Isangel", "Sola", "Lakatoro", "Saratamata", "Longana", "Lenakel", "Port Olry", "Tanna", "Lamap", "Craig Cove", "Lolowai", "Ranon", "Southwest Bay", "Unua", "Vao", "Melsisi", "Wintua"],
    "Vatican City": ["Vatican City", "St. Peter's Square", "Vatican Gardens", "Borgo", "Santa Marta", "Palazzo Apostolico", "Cortile del Belvedere", "Governatorato", "Torre San Giovanni", "Casina Pio IV", "Porta Sant'Anna", "Via della Conciliazione border", "Cortile della Pigna", "Vatican Museums area", "Santa Rosa", "Domus Sanctae Marthae", "Porta Angelica", "Ottavio", "Radio Vaticana", "Governatorato Palace"],
    "Venezuela": ["Caracas", "Maracaibo", "Valencia", "Barquisimeto", "Maracay", "Ciudad Guayana", "San Cristobal", "Maturin", "Barcelona", "Turmero", "Ciudad Bolivar", "Cumana", "Merida", "Cabimas", "Coro", "Puerto La Cruz", "Los Teques", "Guarenas", "Guanare", "Acarigua"],
    "Vietnam": ["Ho Chi Minh City", "Hanoi", "Haiphong", "Da Nang", "Bien Hoa", "Hue", "Nha Trang", "Can Tho", "Vung Tau", "Buon Ma Thuot", "Nam Dinh", "Rach Gia", "Quy Nhon", "Vinh", "Thai Nguyen", "Thanh Hoa", "Hai Duong", "Cam Ranh", "My Tho", "Long Xuyen"],
    "Yemen": ["Sanaa", "Aden", "Taiz", "Al Hudaydah", "Ibb", "Dhamar", "Mukalla", "Amran", "Sayyan", "Zabid", "Saada", "Hajjah", "Bayda", "Marib", "Al Mahwit", "Rada", "Yarim", "Lahij", "Al Ghaydah", "Shibam"],
    "Zambia": ["Lusaka", "Kitwe", "Ndola", "Kabwe", "Chingola", "Mufulira", "Livingstone", "Luanshya", "Kasama", "Chipata", "Solwezi", "Mansa", "Choma", "Mongu", "Kalulushi", "Kafue", "Mazabuka", "Chililabombwe", "Petauke", "Sesheke"],
    "Zimbabwe": ["Harare", "Bulawayo", "Chitungwiza", "Mutare", "Gweru", "Epworth", "Kwekwe", "Kadoma", "Masvingo", "Chinhoyi", "Marondera", "Norton", "Chegutu", "Bindura", "Beitbridge", "Redcliff", "Victoria Falls", "Hwange", "Rusape", "Chiredzi"],
}

# ==========================================
# 2c. City Lookup Build + Manual Overrides
# ==========================================
# Kuch city names duplicate hote hain (e.g. "Valencia" Spain aur Venezuela dono me,
# "San Jose" Costa Rica aur USA dono me). Ye overrides zyada common/likely match ko
# force karte hain jab conflict ho. Job board context me generally US city zyada
# likely hoti hai jab tak location string me khud kisi doosre mulk ka clear signal na ho.
CITY_MANUAL_OVERRIDES = {
    "san jose": ("San Jose", "United States"),
    "san francisco": ("San Francisco", "United States"),
    "new york": ("New York City", "United States"),
    "nyc": ("New York City", "United States"),
    "sf": ("San Francisco", "United States"),
    "la": ("Los Angeles", "United States"),
    "dc": ("Washington D.C.", "United States"),
    "washington dc": ("Washington D.C.", "United States"),
    "washington d.c.": ("Washington D.C.", "United States"),
}

def _build_city_mappings():
    """Do mappings banata hai:
    1. CITY_MAPPING_ALL: city(lowercase) -> [(Display Name, Country), ...] — HAR country jis
       me ye city naam maujood hai (duplicate city names jaise 'London' Canada+UK dono me).
    2. CITY_MAPPING: city(lowercase) -> (Display Name, Country) — default best-guess
       (pehla occurrence, phir manual overrides se overwrite)."""
    all_mapping = {}
    for country, cities in COUNTRY_CITIES.items():
        for city in cities:
            key = city.strip().lower()
            all_mapping.setdefault(key, []).append((city, country))

    default_mapping = {key: candidates[0] for key, candidates in all_mapping.items()}

    # Manual overrides (aliases jaise 'nyc', 'new york', 'sf' jo COUNTRY_CITIES ki asal
    # spelling se alag hain) — inhe default_mapping me override karo AUR all_mapping me
    # bhi daalo (agar wahan pehle se na ho) taake neighbor-based resolution inhe bhi dekh sake.
    for key, value in CITY_MANUAL_OVERRIDES.items():
        default_mapping[key] = value
        if key not in all_mapping:
            all_mapping[key] = [value]
        elif value not in all_mapping[key]:
            all_mapping[key].insert(0, value)

    return all_mapping, default_mapping

CITY_MAPPING_ALL, CITY_MAPPING = _build_city_mappings()
SORTED_CITY_KEYS = sorted(CITY_MAPPING.keys(), key=len, reverse=True)
SORTED_COUNTRY_KEYS = sorted(COUNTRY_MAPPING.keys(), key=len, reverse=True)
IGNORE_WORDS = ["in", "is", "it", "at", "be", "by", "do", "me", "no", "so", "to", "am", "as"]

# ==========================================
# 2d. US Job-Text Detector (fallback signal jab location string me kuch na mile)
# ==========================================
def is_us_job(text):
    if not text:
        return False
    us_patterns = [
        r"\b401\s?\(?k\)?\b",                                  # 401(k)
        r"authorized to work in (the )?(u\.?s\.?a?|united states)\b",
        r"\bE-Verify\b|\bI-9\b",
        r"\bvisa sponsorship (is )?not available\b",
        r"\bEEO\b|\bEqual Opportunity Employer\b",
        r"\b[A-Z][a-zA-Z]+,\s?(CA|NY|TX|FL|WA|IL|PA|OH|GA|NC|MI|NJ|VA|AZ|MA|TN|IN|MO|MD|WI|CO|MN|SC|AL|LA|KY|OR|OK|CT|UT|IA|NV|AR|MS|KS|NM|NE|WV|ID|HI|ME|NH|RI|MT|DE|SD|ND|AK|VT|WY|DC)\b",
        r"\bRemote\s?\(?(US|USA|United States)\)?\b",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in us_patterns)

# ==========================================
# 3. Target Management & File Logging
# ==========================================
def extract_target_info(raw_url):
    url_lower = raw_url.lower()
    
    if "greenhouse.io" in url_lower:
        match = re.search(r'greenhouse\.io/([^/]+)', url_lower)
        if match:
            return "greenhouse", match.group(1)
            
    elif "ashbyhq.com" in url_lower:
        match = re.search(r'ashbyhq\.com/([^/]+)', url_lower)
        if match:
            return "ashby", match.group(1)

    elif "lever.co" in url_lower:
        match = re.search(r'lever\.co/([^/]+)', url_lower)
        if match:
            return "lever", match.group(1)

    elif "apply.workable.com" in url_lower:
        match = re.search(r'apply\.workable\.com/([^/]+)/j/', url_lower)
        if match:
            return "workable", match.group(1)
    return None, None

def lookup_target_in_automatic_file(slug):
    """'automatic.txt' me check karta hai ke kya target mapping majood hai."""
    if not slug or not os.path.exists(TARGET_FILE):
        return None, None
        
    slug_lower = slug.lower()
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        pattern = r'\("([^"]+)",\s*"([^"]+)",\s*"' + re.escape(slug_lower) + r'",\s*".*?"\)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2) # company_name, domain
            
    return None, None

def append_to_must_seen_file(url):
    """Agar URL/slug automatic.txt me nahi mila, to must_seen.txt me log kar do."""
    existing_urls = set()
    if os.path.exists(MUST_SEEN_FILE):
        with open(MUST_SEEN_FILE, "r", encoding="utf-8") as f:
            existing_urls = set(line.strip() for line in f if line.strip())

    if url not in existing_urls:
        with open(MUST_SEEN_FILE, "a", encoding="utf-8") as f:
            f.write(f"{url}\n")
        print(f"📌 Added URL to '{MUST_SEEN_FILE}' for manual review.")
def get_company_job_count(slug):
    """company_limit.txt se is slug ka current count nikalta hai."""
    if not os.path.exists(COMPANY_LIMIT_FILE):
        return 0
    slug_lower = slug.lower()
    with open(COMPANY_LIMIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) == 2 and parts[0].strip().lower() == slug_lower:
                try:
                    return int(parts[1].strip())
                except ValueError:
                    return 0
    return 0

def increment_company_job_count(slug):
    """Job successfully post hone ke baad slug ka count +1 karta hai."""
    slug_lower = slug.lower()
    lines = []
    if os.path.exists(COMPANY_LIMIT_FILE):
        with open(COMPANY_LIMIT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(":")
        if len(parts) == 2 and parts[0].strip().lower() == slug_lower:
            current_count = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
            new_lines.append(f"{parts[0].strip()}:{current_count + 1}\n")
            found = True
        else:
            new_lines.append(f"{stripped}\n")

    if not found:
        new_lines.append(f"{slug_lower}:1\n")

    with open(COMPANY_LIMIT_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
def process_alert_tracking(tags, matched_countries_str):
    if not tags:
        return []

    top_4_tags = tags[:4]

    # "Remote (United States(New York City), Germany(Berlin))" jaisi nested-bracket
    # string se sirf country names nikalta hai (city part ko ignore karke), taake
    # comma-split city ke andar wale comma se na tootay.
    inner = matched_countries_str.strip()
    if inner.startswith("Remote ("):
        inner = inner[len("Remote ("):]
    if inner.endswith(")"):
        inner = inner[:-1]

    raw_parts = re.findall(r'[^,()]+(?:\([^()]*\))?', inner)
    countries = []
    for part in raw_parts:
        country_name = re.sub(r'\(.*\)', '', part).strip()
        if country_name:
            countries.append(country_name)

    if not countries:
        countries = ["United States"]

    existing_alerts = set()
    if os.path.exists(ALERT_TRACKING_FILE):
        with open(ALERT_TRACKING_FILE, "r", encoding="utf-8") as f:
            for line in f:
                existing_alerts.add(line.strip().lower())

    new_alerts_to_add = []
    final_alert_tags = []

    for tag in top_4_tags:
        for country in countries:
            alert_key = f"{tag.strip().lower()} | {country.strip().lower()}"
            if alert_key not in existing_alerts:
                new_alerts_to_add.append(f"{tag.strip()} | {country.strip()}\n")
                existing_alerts.add(alert_key)
                if tag not in final_alert_tags:
                    final_alert_tags.append(tag)

    if new_alerts_to_add:
        with open(ALERT_TRACKING_FILE, "a", encoding="utf-8") as f:
            f.writelines(new_alerts_to_add)

    return final_alert_tags

# ==========================================
# 4. Helper Formatting Functions
# ==========================================
def _match_countries_in_segment(segment):
    """Ek segment (comma se split hua ek piece) me se saare country matches nikalta hai.
    Match hone ke baad us word ko text se hata deta hai taake overlapping shorter keys
    dobara match na karein."""
    seg_lower = segment.lower()
    found = []
    for key in SORTED_COUNTRY_KEYS:
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, seg_lower):
            # US aur UK ko strictly capitals me check karega
            if key == "us" and not re.search(r'\bUS\b', segment):
                continue
            if key == "uk" and not re.search(r'\bUK\b', segment):
                continue
            # Agar 'in', 'it' jaisa word hai toh strictly Capital letters me verify karega
            if key in IGNORE_WORDS and not re.search(r'\b' + key.upper() + r'\b', segment):
                continue

            country = COUNTRY_MAPPING[key]
            if country not in found:
                found.append(country)
            seg_lower = re.sub(pattern, ' ', seg_lower)  # match hone ke baad word hata do
    return found

def _find_city_key(segment):
    """Segment me se pehli city key (lowercase) dhoondta hai, longest-match priority ke saath."""
    seg_lower = segment.lower()
    for key in SORTED_CITY_KEYS:
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, seg_lower):
            return key
    return None

def format_location(loc_input, job_text=""):
    """
    Priority order:
      1. Har comma-separated segment me pehle COUNTRY match try karta hai.
      2. Agar us segment me country na mile, phir CITY match try karta hai
         (city mile to us city ke desh ke saath 'Country(City)' format me add hota hai).
      3. Agar location string me se kuch bhi (na country na city) match na ho,
         to job description text me se US-indicator regex check karta hai
         (401k, EEO, E-Verify, US state jaisi patterns) — match mile to 'Remote (United States)'.
      4. Agar wahan bhi kuch na mile to sirf 'Remote (Global)' return karta hai.
    """
    def fallback():
        if job_text and is_us_job(job_text):
            return "Remote (United States)"
        return "Remote (Global)"

    if not loc_input or not loc_input.strip():
        return fallback()

    loc_stripped = loc_input.strip()
    if loc_stripped.lower() in ("global", "remote (global)", "worldwide", "anywhere"):
      return "Remote (Global)"

    if loc_stripped.lower() == "remote":
      return fallback()   # ab ye job_text me 401k/EEO/etc check karega

    segments = [s.strip() for s in loc_stripped.split(",") if s.strip()]
    if not segments:
        segments = [loc_stripped]

    country_order = []          # jis order me countries mile
    country_cities_found = {}   # country -> [cities]

    # PASS 1: pehle saare segments se explicit country matches nikal lo (city resolve
    # karte waqt in par priority di jayegi — e.g. "San Jose, Costa Rica" me Costa Rica
    # explicitly likha hai to San Jose ko US ke bajaye Costa Rica se jorenge)
    segment_countries = [_match_countries_in_segment(segment) for segment in segments]
    explicit_countries = set(c for countries in segment_countries for c in countries)

    # PASS 2: ab har segment ko process karo — country mila to seedha add karo,
    # warna city try karo. City ke multiple-country conflicts (jaise 'London' Canada+UK,
    # 'San Jose' Costa Rica+USA) resolve karne ki priority:
    #   1. Immediate agla ya pichla segment (jo khud us city ka candidate country ho)
    #   2. Warna poori string me kahi bhi mila explicit country
    #   3. Warna manual override / pehla default guess
    for idx, (segment, countries_in_seg) in enumerate(zip(segments, segment_countries)):
        if countries_in_seg:
            for country in countries_in_seg:
                if country not in country_cities_found:
                    country_cities_found[country] = []
                    country_order.append(country)
            continue

        city_key = _find_city_key(segment)
        if not city_key:
            continue

        candidates = CITY_MAPPING_ALL.get(city_key, [])
        if not candidates:
            continue

        chosen = None
        neighbor_indices = [i for i in (idx + 1, idx - 1) if 0 <= i < len(segments)]
        for n_idx in neighbor_indices:
            neighbor_countries = segment_countries[n_idx]
            match = next((c for c in candidates if c[1] in neighbor_countries), None)
            if match:
                chosen = match
                break

        if not chosen:
            match = next((c for c in candidates if c[1] in explicit_countries), None)
            if match:
                chosen = match

        if not chosen:
            chosen = CITY_MAPPING.get(city_key)

        if chosen:
            city_display, country = chosen
            if country not in country_cities_found:
                country_cities_found[country] = []
                country_order.append(country)
            if city_display not in country_cities_found[country]:
                country_cities_found[country].append(city_display)

    if not country_order:
        return fallback()

    parts = []
    for country in country_order:
        cities = country_cities_found[country]
        if cities:
            parts.append(f"{country}({', '.join(cities)})")
        else:
            parts.append(country)

    return f"Remote ({', '.join(parts)})"

def build_ats_url(raw_url):
    parsed = urlparse(raw_url)
    utm_params = {
        'utm_source': 'hireskys.com',
        'utm_medium': 'job_board',
        'utm_campaign': 'hireskys_remote_alerts'
    }
    query = dict(parse_qsl(parsed.query))
    query.update(utm_params)
    new_url = parsed._replace(query=urlencode(query))
    return new_url.geturl()

def process_job_with_ai(raw_text, retries=3):
    prompt = f"""
    The user has pasted the entire job posting, including the job title, metadata, and the job description.
    Extract the information into a valid JSON object.
    
    Rules:
    1. 'title': Extract the clean job title from the text.
    2. 'description': The core job description. Format it STRICTLY in clean HTML (use <p>, <h3>, <ul>, <li>, <b>).
       CRITICAL INSTRUCTIONS FOR DESCRIPTION:
       - CLEANUP: First, REMOVE all irrelevant top-level metadata and duplicate headers.
       - PRESERVE CORE: Keep every single detail, paragraph exactly as it is. DO NOT summarize.
       - SMART BOLDING: Only bold hard facts (tech, experience years, metrics).
    3. 'category': Pick EXACTLY ONE main category from this list: {list(CATEGORIES_MAP.keys())}.
    4. 'tags': Pick up to 5 relevant sub-categories from this list: {json.dumps(CATEGORIES_MAP)}. Output as a list of strings.
    5. 'salary_range': Extract compensation if available, otherwise "Not Disclosed".
    6. 'job_type': "Full-time", "Part-time", "Contract", or "Freelance".
    7. 'experience_level': "Entry-Level", "Mid-Level", "Senior-Level", or "Lead/Manager".

    Raw Job Post:
    {raw_text}
    """
    
    for attempt in range(retries):
        try:
            response = mistral_client.chat.complete(
                model='mistral-large-latest',
                response_format={ "type": "json_object" },
                temperature=0.1,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": "You are a data extraction AI. Output ONLY a valid JSON object."},
                    {"role": "user", "content": prompt}
                ]
            )
            raw_result = response.choices[0].message.content
            if raw_result:
                return json.loads(raw_result)
        except Exception as e:
            ...
            if 'rate limit' in str(e).lower() or '429' in str(e).lower():
                time.sleep(60)
            else:
                return None
    return None

def get_company_domain(company_name):
    try:
        url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={company_name}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['domain']
    except Exception:
        pass
    return None

# ==========================================
# 5. ATS Direct Fetchers
# ==========================================
def fetch_greenhouse_job(frontend_url):
    parts = frontend_url.strip('/').split('/')
    try:
        job_id = parts[-1]
        board_token = parts[-3] 
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"
        
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        company_name = data.get('company_name', board_token.capitalize())
            
        return {
            "company_name": company_name,
            "location": data.get('location', {}).get('name', 'Remote'),
            "content": data.get('content', ''),
            "url": data.get('absolute_url', frontend_url)
        }
    except Exception as e:
        print(f"❌ Error parsing Greenhouse URL: {e}")
        return None
    
def fetch_ashby_job(frontend_url):
    parts = frontend_url.split('?')[0].strip('/').split('/')
    try:
        job_id = parts[-1]
        company_name = parts[-3] if job_id.lower() == 'application' else parts[-2]
        if job_id.lower() == 'application':
            job_id = parts[-2]
        
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{company_name}"
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return None
            
        jobs_array = response.json().get('jobs', [])
        target_job = next((j for j in jobs_array if j.get('id') == job_id), None)
        if not target_job:
            return None

        # 🚨 ASHBY HYBRID REJECTION 🚨
        workplace_type = str(target_job.get('workplaceType', '')).lower()
        
        # 🟢 MULTIPLE LOCATIONS EXTRACTION LOGIC 🟢
        locations_list = []
        
        # 1. Primary Location uthao
        primary_loc = target_job.get('location')
        if primary_loc:
            locations_list.append(primary_loc)
            
        # 2. Secondary Locations uthao (Agar multiple countries hain)
        secondary_locs = target_job.get('secondaryLocations', [])
        if isinstance(secondary_locs, list):
            for sec in secondary_locs:
                sec_loc_name = sec.get('location')
                if sec_loc_name:
                    locations_list.append(sec_loc_name)
                    
        # 3. Sab ko comma se jor do (e.g. "USA, Canada, UK")
        full_location_string = ", ".join(locations_list) if locations_list else 'Remote'

        # Hybrid location word check
        if workplace_type == 'hybrid' or 'hybrid' in full_location_string.lower():
            print(f"🚫 ASHBY HYBRID REJECTED: '{target_job.get('title')}'")
            return "HYBRID_REJECTED"
            
        return {
            "company_name": company_name.capitalize(),
            "location": full_location_string, # Ab ye saari locations pass karega
            "content": target_job.get('descriptionHtml', ''),
            "url": f"https://jobs.ashbyhq.com/{company_name}/{job_id}/application"
        }
    except Exception as e:
        print(f"❌ Error parsing Ashby URL: {e}")
        return None

def fetch_lever_job(frontend_url):
    parts = frontend_url.split('?')[0].strip('/').split('/')
    try:
        job_id = parts[-1]
        company_name = parts[-3] if job_id.lower() == 'apply' else parts[-2]
        if job_id.lower() == 'apply':
            job_id = parts[-2]
            
        api_url = f"https://api.lever.co/v0/postings/{company_name}/{job_id}"
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        raw_html_content = data.get('description', '')
        for lst in data.get('lists', []):
            if lst.get('text'):
                raw_html_content += f"<h3>{lst.get('text')}</h3>"
            raw_html_content += lst.get('content', '')
            
        if data.get('additional'):
            raw_html_content += f"<br>{data.get('additional')}"
            
        return {
            "company_name": company_name.capitalize(),
            "location": data.get('categories', {}).get('location', 'Remote'),
            "content": raw_html_content,
            "url": data.get('applyUrl', f"https://jobs.lever.co/{company_name}/{job_id}/apply")
        }
    except Exception as e:
        print(f"❌ Error parsing Lever URL: {e}")
        return None

def fetch_workable_job(frontend_url):
    parts = frontend_url.split('?')[0].strip('/').split('/')
    try:
        # Expected shape: https://apply.workable.com/{slug}/j/{shortcode}
        j_index = parts.index('j')
        shortcode = parts[j_index + 1]
        slug = parts[j_index - 1]

        api_url = f"https://apply.workable.com/api/v2/accounts/{slug}/jobs/{shortcode}"
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()

        # 🚨 WORKABLE HYBRID REJECTION 🚨
        workplace_type = str(data.get('workplace', '')).lower()
        if workplace_type == 'hybrid':
            print(f"🚫 WORKABLE HYBRID REJECTED: '{data.get('title')}'")
            return "HYBRID_REJECTED"

        content_html = data.get('description', '') or ''
        requirements = data.get('requirements', '')
        benefits = data.get('benefits', '')
        if requirements:
            content_html += f"<h3>Requirements</h3>{requirements}"
        if benefits:
            content_html += f"<h3>Benefits</h3>{benefits}"

        loc = data.get('location', {}) or {}
        location_str = loc.get('country') or 'Remote'

        return {
            "company_name": slug.capitalize(),
            "location": location_str,
            "content": content_html,
            "url": data.get('shortlink') or frontend_url
        }
    except Exception as e:
        print(f"❌ Error parsing Workable URL: {e}")
        return None


def add_new_job_automated(raw_job_text, company_name, company_domain, location_input, raw_ats_url):
    ai_data = process_job_with_ai(raw_job_text)
    if not ai_data:
        print("❌ AI Failed to format job details.")
        return False
        
    final_location = format_location(location_input, raw_job_text)
    logo_url = f"https://img.logo.dev/{company_domain}?token=pk_aH9IPqwYQqW08DI-epK7yw&size=200&format=png"
    final_url = build_ats_url(raw_ats_url)
    
    tags = ai_data.get('tags', [])
    alert_tags = process_alert_tracking(tags, final_location)

    db_payload = {
        "title": ai_data.get('title', 'Untitled Job'),
        "source": company_name,
        "link": final_url,
        "category": ai_data.get('category', 'Other'),
        "date_posted": datetime.now(timezone.utc).isoformat(),
        "platform": "Web",
        "description": ai_data.get('description', ''),
        "location": final_location,
        "salary_range": ai_data.get('salary_range', 'Not Disclosed'),
        "job_type": ai_data.get('job_type', 'Full-time'),
        "application_count": 0,
        "tags": list(set(tags + alert_tags)), 
        "approved": True, 
        "is_verified": True,
        "active": True,
        "experience_level": ai_data.get('experience_level', 'Mid-Level'),
        "company_logo_url": logo_url
    }
    
    try:
        # Insert — Supabase 'select' chain ke bina hi poori row (id/created_at/slug
        # samet) wapas deta hai. Ye row Supabase me save hote hi tumhara webhook
        # route ise automatically Typesense me sync kar dega — koi manual Gist
        # push ki zaroorat nahi.
        result = supabase.table('jobs').insert(db_payload).execute()

        print(f"✅ Success! Posted '{db_payload['title']}' for {company_name} ({final_location})")
        return True
    except Exception as e:
        print(f"❌ Database Insertion Error: {e}")
        return False

# ==========================================
# 7. Automated Engine Runner (REAL-TIME MODE)
# ==========================================
PROCESSED_FILE = "processed_seen_jobs.txt"   # kaunse URLs already handle ho chuke hain, iska record
POLL_INTERVAL = 5   # kitne seconds baad seen_jobs.txt ko dobara check kare

def load_processed_urls():
    """Pehle se process ho chuke URLs ko disk se load karta hai (restart-safe)."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def mark_url_processed(url):
    """URL ko processed_seen_jobs.txt me permanently likh deta hai taake dobara na uthe."""
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")

def process_single_url(raw_ats_url):
    """Ek single URL ke liye poori pipeline chalata hai. Returns True agar job actually post hui."""
    platform, slug = extract_target_info(raw_ats_url)

    if not platform or not slug:
        print("⚠️ Skipped: Link is not from Ashby, Lever, Greenhouse, or Workable.")
        return False

    # 1. Lookup target in automatic.txt
    mapped_name, mapped_domain = lookup_target_in_automatic_file(slug)

    if not mapped_name:
        print(f"🔍 Target slug '{slug}' not found in 'automatic.txt'. Logging URL and SKIPPING.")
        append_to_must_seen_file(raw_ats_url)
        return False

    current_count = get_company_job_count(slug)
    if current_count >= MAX_JOBS_PER_COMPANY:
        print(f"🚫 Company '{slug}' has reached the limit ({current_count}/{MAX_JOBS_PER_COMPANY}). Skipping this job.")
        return False

    job_data = None
    if platform == "greenhouse":
        job_data = fetch_greenhouse_job(raw_ats_url)
    elif platform == "ashby":
        job_data = fetch_ashby_job(raw_ats_url)
    elif platform == "lever":
        job_data = fetch_lever_job(raw_ats_url)
    elif platform == "workable":
        job_data = fetch_workable_job(raw_ats_url)

    if job_data == "HYBRID_REJECTED":
        return False

    if not job_data:
        print("❌ Failed to fetch job details from ATS API.")
        return False

    success = add_new_job_automated(
        raw_job_text=job_data['content'],
        company_name=mapped_name,
        company_domain=mapped_domain,
        location_input=job_data['location'],
        raw_ats_url=job_data['url']
    )

    if success:
        increment_company_job_count(slug)

    return success

def run_realtime_watcher():
    print("\n" + "="*50)
    print("🚀 REAL-TIME JOB POSTER ENGINE STARTED")
    print("👀 Watching 'seen_jobs.txt' — Ctrl+C dabane tak chalta rahega")
    print("="*50 + "\n")

    processed = load_processed_urls()
    print(f"📂 {len(processed)} URLs pehle se processed mil gaye (in ko skip kiya jayega).\n")

    while True:
        try:
            if not os.path.exists(SEEN_JOBS_FILE):
                time.sleep(POLL_INTERVAL)
                continue

            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                job_urls = [line.strip() for line in f if line.strip()]

            new_urls = [u for u in job_urls if u not in processed]

            if not new_urls:
                # Kuch naya nahi mila, thodi der sokar dobara check karo
                time.sleep(POLL_INTERVAL)
                continue

            for raw_ats_url in new_urls:
                print(f"\n--- 🆕 New URL detected: {raw_ats_url} ---")
                success = process_single_url(raw_ats_url)

                # Chahe post ho ya skip ho, isko processed mark kar do taake dobara na uthe
                processed.add(raw_ats_url)
                mark_url_processed(raw_ats_url)

                if success:
                    sleep_time = random.randint(20, 30)
                    print(f"⏳ Waiting {sleep_time} seconds before checking for the next job...")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n🛑 Terminal se rok diya gaya. Engine band ho raha hai. Bye!")
            break
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}. {POLL_INTERVAL} seconds baad retry karega...")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_realtime_watcher()

"""Merchant catalog suggestions. These are unpublished until the owner activates them."""
CATALOG = [
 ('staples','Grains, Flours & Pulses','અનાજ, લોટ અને કઠોળ','🌾',[
  ('Rice','ચોખા','Basmati|બાસમતી;Kolam|કોલમ;Sona Masoori|સોના મસૂરી;Indrayani|ઇન્દ્રાયણી;Ambemohar|આંબેમોહર;Parmal|પરમલ;Brown rice|બ્રાઉન રાઇસ'),
  ('Wheat & Millets','ઘઉં અને બાજરી','Loose wheat|છૂટા ઘઉં;Sharbati wheat|શરબતી ઘઉં;Lokwan wheat|લોકવણ ઘઉં;Bajra|બાજરી;Jowar|જુવાર;Ragi|રાગી;Makai|મકાઈ;Kodo millet|કોડો;Foxtail millet|કાંગ'),
  ('Poha & Semolina','પૌંઆ અને રવો','Thick poha|જાડા પૌંઆ;Thin poha|પાતળા પૌંઆ;Murmura|મમરા;Sabudana|સાબુદાણા;Dalia|દલિયા;Fine rava|ઝીણો રવો;Coarse rava|જાડો રવો;Vermicelli|સેવૈયાં'),
  ('Wheat Flours','ઘઉંનો લોટ','Loose atta|છૂટો ઘઉંનો લોટ;Branded atta|બ્રાન્ડેડ ઘઉંનો લોટ;Maida|મેંદો;Whole wheat flour|આખા ઘઉંનો લોટ'),
  ('Other Flours','બીજા લોટ','Besan|બેસન;Rice flour|ચોખાનો લોટ;Bajra flour|બાજરીનો લોટ;Jowar flour|જુવારનો લોટ;Ragi flour|રાગીનો લોટ;Makai flour|મકાઈનો લોટ;Sattu|સત્તુ'),
  ('Instant Flour Mixes','તૈયાર લોટ મિક્સ','Dhokla flour|ઢોકળાનો લોટ;Khaman mix|ખમણ મિક્સ;Handvo flour|હાંડવાનો લોટ;Thepla atta|થેપલાનો લોટ;Multigrain atta|મલ્ટિગ્રેન લોટ'),
  ('Split Dals','દાળ','Tuver dal|તુવેર દાળ;Yellow moong dal|મગની પીળી દાળ;Chana dal|ચણાની દાળ;White urad dal|સફેદ અડદ દાળ;Masoor dal|મસૂર દાળ'),
  ('Dals with Skin','છાલવાળી દાળ','Moong chilka|છાલવાળા મગ;Urad chilka|છાલવાળા અડદ;Masoor with skin|છાલવાળી મસૂર'),
  ('Whole Pulses','આખા કઠોળ','Whole moong|આખા મગ;Matki|મઠ;Chawli|ચોળી;Kala chana|કાળા ચણા;Whole urad|આખા અડદ'),
  ('Beans & Peas','કઠોળ અને વટાણા','Rajma|રાજમા;Kabuli chana|કાબુલી ચણા;White vatana|સફેદ વટાણા;Green vatana|લીલા વટાણા;Vaal|વાલ')]),
 ('oils','Oils, Ghee & Sweeteners','તેલ, ઘી અને મીઠાશ','🫙',[
  ('Cooking Oils','રસોઈનાં તેલ','Groundnut oil|સીંગતેલ;Cottonseed oil|કપાસિયા તેલ;Sunflower oil|સૂર્યમુખી તેલ;Soybean oil|સોયાબીન તેલ;Mustard oil|રાઈનું તેલ;Rice bran oil|રાઇસ બ્રાન તેલ;Palm oil|પામ તેલ'),
  ('Specialty Oils','ખાસ તેલ','Coconut oil|નાળિયેર તેલ;Sesame oil|તલનું તેલ;Olive oil|ઓલિવ તેલ'),
  ('Ghee & Fats','ઘી અને ચરબી','Cow ghee|ગાયનું ઘી;Buffalo ghee|ભેંસનું ઘી;Vanaspati|વનસ્પતિ ઘી'),
  ('Salt','મીઠું','Iodised salt|આયોડાઇઝ્ડ મીઠું;Rock salt|સિંધવ મીઠું;Black salt|સંચળ;Sea salt|દરિયાઈ મીઠું'),
  ('Sugar','ખાંડ','Regular sugar|ખાંડ;Sulphur-free sugar|સલ્ફર મુક્ત ખાંડ;Khadi sakar|ખડી સાકર;Brown sugar|બ્રાઉન સુગર;Icing sugar|આઇસિંગ સુગર'),
  ('Jaggery & Honey','ગોળ અને મધ','Jaggery block|ગોળ;Powder jaggery|ગોળનો ભૂકો;Liquid jaggery|પ્રવાહી ગોળ;Honey|મધ;Sugar-free sweetener|શુગર ફ્રી મીઠાશ')]),
 ('spices','Spices & Masalas','મસાલા','🌶️',[
  ('Whole Spices','આખા મસાલા','Mustard seeds|રાઈ;Cumin|જીરું;Fenugreek|મેથી દાણા;Ajwain|અજમો;Fennel|વરિયાળી;Coriander seeds|ધાણા;Sesame|તલ;Poppy seeds|ખસખસ'),
  ('Garam Spices','ગરમ મસાલા','Cloves|લવિંગ;Cinnamon|તજ;Green cardamom|લીલી એલચી;Black cardamom|કાળી એલચી;Bay leaf|તમાલપત્ર;Star anise|બાદિયાન;Black pepper|કાળા મરી;Nutmeg|જાયફળ'),
  ('Powdered Spices','ભૂકા મસાલા','Turmeric powder|હળદર પાવડર;Kashmiri chilli powder|કાશ્મીરી મરચું પાવડર;Red chilli powder|લાલ મરચું પાવડર;Coriander powder|ધાણા પાવડર;Cumin powder|જીરું પાવડર;Dhana-jeeru|ધાણા જીરું'),
  ('Other Spices','બીજા મસાલા','Hing|હિંગ;Dry red chillies|સૂકા લાલ મરચાં;Dry ginger|સૂંઠ;Kokum|કોકમ;Tamarind|આમલી'),
  ('Everyday Masalas','રોજના મસાલા','Garam masala|ગરમ મસાલો;Sambhar masala|સાંભાર મસાલો;Chaat masala|ચાટ મસાલો;Chai masala|ચા મસાલો'),
  ('Vegetable Masalas','શાકના મસાલા','Pav bhaji masala|પાવભાજી મસાલો;Undhiyu masala|ઊંધિયું મસાલો;Dal-shaak masala|દાળ શાક મસાલો;Chole masala|છોલે મસાલો;Kitchen King masala|કિચન કિંગ મસાલો'),
  ('Pickle & Snack Masalas','અથાણા અને નાસ્તાના મસાલા','Athanu masala|અથાણાનો મસાલો;Methia masala|મેથીયા મસાલો;Chevdo masala|ચેવડા મસાલો;Sev-usal masala|સેવ ઉસળ મસાલો')]),
 ('dryfruits','Dry Fruits, Seeds & Sweets','સૂકા મેવા અને મીઠાઈ','🥜',[
  ('Nuts','સૂકા મેવા','Almonds|બદામ;Cashews|કાજુ;Pistachios|પિસ્તા;Walnuts|અખરોટ;Raw peanuts|કાચી મગફળી;Roasted peanuts|શેકેલી મગફળી;Chironji|ચારોળી'),
  ('Dried Fruits','સૂકાં ફળ','Raisins|કિસમિસ;Dates|ખજૂર;Figs|અંજીર;Apricots|જરદાળુ;Prunes|સૂકા આલુ'),
  ('Seeds & Others','બીજ અને અન્ય','Watermelon seeds|તરબૂચના બીજ;Pumpkin seeds|કોળાના બીજ;Sunflower seeds|સૂર્યમુખીનાં બીજ;Flax seeds|અળસી;Chia seeds|ચિયા બીજ;Dry coconut|સૂકું નાળિયેર;Makhana|મખાણા'),
  ('Traditional Sweets','પરંપરાગત મીઠાઈ','Peanut chikki|મગફળીની ચીકી;Til chikki|તલની ચીકી;Laddu|લાડુ;Sukhdi|સુખડી;Mohanthal|મોહનથાળ'),
  ('Sweet Mixes & Baking','મીઠાઈ મિક્સ અને બેકિંગ','Gulab jamun mix|ગુલાબજાંબુ મિક્સ;Jalebi mix|જલેબી મિક્સ;Custard powder|કસ્ટર્ડ પાવડર;Kheer mix|ખીર મિક્સ;Baking powder|બેકિંગ પાવડર;Baking soda|બેકિંગ સોડા;Cocoa powder|કોકો પાવડર;Food colour|ફૂડ કલર;Essence|એસેન્સ')]),
 ('beverages','Tea, Coffee & Beverages','ચા, કોફી અને પીણાં','☕',[
  ('Tea','ચા','Loose tea|છૂટી ચા;Packet tea|પેકેટ ચા;Green tea|ગ્રીન ટી;Masala tea|મસાલા ચા;Tea bags|ટી બેગ'),
  ('Coffee','કોફી','Instant coffee|ઇન્સ્ટન્ટ કોફી;Filter coffee|ફિલ્ટર કોફી;Coffee premix|કોફી પ્રિમિક્સ'),
  ('Health Drinks','હેલ્થ ડ્રિંક્સ','Bournvita|બોર્નવિટા;Horlicks|હોર્લિક્સ;Boost|બૂસ્ટ;Complan|કોમ્પ્લાન'),
  ('Cold Drinks & Juices','ઠંડાં પીણાં અને જ્યૂસ','Soft drinks|સોફ્ટ ડ્રિંક;Packaged juices|પેકેટ જ્યૂસ;Soda|સોડા;Packaged water|પેકેટ પાણી'),
  ('Syrups & Squashes','શરબત','Rose syrup|ગુલાબ શરબત;Lemon squash|લીંબુ સ્ક્વોશ;Sharbat concentrate|શરબત કોન્સન્ટ્રેટ')]),
 ('snacks','Packaged Foods & Snacks','પેકેટ ખોરાક અને નાસ્તા','🍪',[
  ('Noodles & Pasta','નૂડલ્સ અને પાસ્તા','Instant noodles|ઇન્સ્ટન્ટ નૂડલ્સ;Macaroni|મેકરોની;Spaghetti|સ્પેગેટી;Pasta|પાસ્તા'),
  ('Breakfast Cereals','નાસ્તાના સિરિયલ','Cornflakes|કોર્નફ્લેક્સ;Oats|ઓટ્સ;Muesli|મ્યુસલી;Chocos|ચોકોઝ'),
  ('Biscuits & Cookies','બિસ્કિટ અને કૂકીઝ','Glucose biscuits|ગ્લુકોઝ બિસ્કિટ;Cream biscuits|ક્રીમ બિસ્કિટ;Marie biscuits|મેરી બિસ્કિટ;Salted biscuits|ખારા બિસ્કિટ;Cookies|કૂકીઝ;Rusk|ટોસ્ટ બિસ્કિટ'),
  ('Chips & Wafers','ચિપ્સ અને વેફર્સ','Potato chips|બટાકાની ચિપ્સ;Banana wafers|કેળાની વેફર્સ;Namkeen packets|નમકીન પેકેટ'),
  ('Chocolates & Candies','ચોકલેટ અને કેન્ડી','Chocolates|ચોકલેટ;Toffees|ટોફી;Mints|મિન્ટ;Chewing gum|ચીંગમ'),
  ('Gujarati Farsan','ગુજરાતી ફરસાણ','Gathiya|ગાંઠિયા;Fafda|ફાફડા;Chakri|ચકરી;Bhakarwadi|ભાખરવડી;Mathri|મઠરી;Chevdo|ચેવડો;Sev mamra|સેવ મમરા;Mixture|મિક્સચર;Dry kachori|સૂકી કચોરી'),
  ('Khakhra','ખાખરા','Plain khakhra|સાદા ખાખરા;Methi khakhra|મેથી ખાખરા;Jeera khakhra|જીરા ખાખરા;Masala khakhra|મસાલા ખાખરા;Bajra khakhra|બાજરી ખાખરા'),
  ('Papad','પાપડ','Udad papad|અડદના પાપડ;Moong papad|મગના પાપડ;Sabudana papad|સાબુદાણાના પાપડ;Rice papad|ચોખાના પાપડ;Fryums|ફ્રાયમ્સ'),
  ('Packaged Thepla & Puri','પેકેટ થેપલા અને પૂરી','Methi thepla|મેથીના થેપલા;Plain thepla|સાદા થેપલા;Puri|પૂરી'),
  ('Instant Cooking Mixes','ઇન્સ્ટન્ટ મિક્સ','Idli mix|ઇડલી મિક્સ;Dosa mix|ઢોસા મિક્સ;Upma mix|ઉપમા મિક્સ;Khichdi mix|ખીચડી મિક્સ')]),
 ('fresh','Dairy, Bakery & Fresh Produce','ડેરી, બેકરી અને તાજી વસ્તુઓ','🥛',[
  ('Milk','દૂધ','Full cream milk|ફુલ ક્રીમ દૂધ;Toned milk|ટોન્ડ દૂધ;Double toned milk|ડબલ ટોન્ડ દૂધ;Flavoured milk|ફ્લેવર્ડ દૂધ'),
  ('Curd & Buttermilk','દહીં અને છાશ','Curd|દહીં;Chaas|છાશ;Lassi|લસ્સી;Shrikhand|શ્રીખંડ'),
  ('Cheese, Paneer & Butter','ચીઝ, પનીર અને માખણ','Paneer|પનીર;Cheese slices|ચીઝ સ્લાઇસ;Cheese cubes|ચીઝ ક્યુબ;Cheese spread|ચીઝ સ્પ્રેડ;Mozzarella|મોઝરેલા;Butter|માખણ;Fresh cream|તાજી ક્રીમ'),
  ('Frozen','ફ્રોઝન','Ice cream|આઇસ્ક્રીમ;Kulfi|કુલ્ફી;Frozen peas|ફ્રોઝન વટાણા;Frozen snacks|ફ્રોઝન નાસ્તા'),
  ('Bread & Bakery','બ્રેડ અને બેકરી','White bread|સફેદ બ્રેડ;Brown bread|બ્રાઉન બ્રેડ;Multigrain bread|મલ્ટિગ્રેન બ્રેડ;Ladi pav|લાડી પાવ;Burger buns|બર્ગર બન;Cake slices|કેક સ્લાઇસ;Muffins|મફિન;Toast|ટોસ્ટ'),
  ('Staple Vegetables','રોજનાં શાક','Potato|બટાકા;Onion|ડુંગળી;Tomato|ટામેટાં;Garlic|લસણ;Ginger|આદુ'),
  ('Other Vegetables','બીજાં શાક','Coriander leaves|કોથમીર;Methi leaves|મેથીની ભાજી;Palak|પાલક;Brinjal|રીંગણ;Lady finger|ભીંડા;Cauliflower|ફૂલકોબી;Cabbage|કોબી;Gourds|દૂધી અને તૂરિયા;Capsicum|કેપ્સિકમ'),
  ('Fruits','ફળ','Banana|કેળાં;Apple|સફરજન;Orange|નારંગી;Papaya|પપૈયું;Mango|કેરી;Chikoo|ચીકુ'),
  ('Fresh Others','અન્ય તાજી વસ્તુઓ','Green chillies|લીલા મરચાં;Lemon|લીંબુ;Curry leaves|મીઠો લીમડો')]),
 ('condiments','Pickles, Sauces & Condiments','અથાણાં, સોસ અને ચટણીઓ','🥫',[
  ('Pickles','અથાણાં','Mango pickle|કેરીનું અથાણું;Lemon pickle|લીંબુનું અથાણું;Mixed pickle|મિક્સ અથાણું;Methia keri|મેથીયા કેરી;Chhundo|છૂંદો;Gor keri|ગોર કેરી;Green chilli pickle|લીલા મરચાંનું અથાણું'),
  ('Sauces','સોસ','Tomato ketchup|ટામેટાં કેચપ;Soy sauce|સોયા સોસ;Green chilli sauce|લીલા મરચાંનો સોસ;Red chilli sauce|લાલ મરચાંનો સોસ;Schezwan sauce|શેઝવાન સોસ;Mayonnaise|મેયોનેઝ;Mustard sauce|મસ્ટર્ડ સોસ'),
  ('Spreads','સ્પ્રેડ','Jam|જામ;Peanut butter|પીનટ બટર;Chocolate spread|ચોકલેટ સ્પ્રેડ'),
  ('Condiment Others','બીજી ચટણીઓ','Vinegar|વિનેગર;Tamarind paste|આમલીની પેસ્ટ')]),
 ('care','Personal Care & Baby Care','અંગત સંભાળ અને બેબી કેર','🧼',[
  ('Soap','સાબુ','Lux soap|લક્સ સાબુ;Dettol soap|ડેટોલ સાબુ;Lifebuoy soap|લાઇફબોય સાબુ;Santoor soap|સંતૂર સાબુ;Pears soap|પિયર્સ સાબુ;Cinthol soap|સિન્થોલ સાબુ;Dove soap|ડવ સાબુ;Medimix soap|મેડિમિક્સ સાબુ;Margo soap|માર્ગો સાબુ;Hand wash|હેન્ડ વૉશ'),
  ('Hair Care','વાળની સંભાળ','Shampoo|શેમ્પૂ;Conditioner|કન્ડિશનર;Coconut hair oil|નાળિયેરનું વાળનું તેલ;Amla hair oil|આમળાનું તેલ;Almond hair oil|બદામનું તેલ;Hair colour|હેર કલર;Mehendi|મહેંદી'),
  ('Oral Care','દાંતની સંભાળ','Colgate toothpaste|કોલગેટ ટૂથપેસ્ટ;Pepsodent toothpaste|પેપ્સોડેન્ટ ટૂથપેસ્ટ;Dabur Red toothpaste|ડાબર રેડ ટૂથપેસ્ટ;Close-up toothpaste|ક્લોઝઅપ ટૂથપેસ્ટ;Toothbrush|ટૂથબ્રશ;Mouthwash|માઉથવૉશ;Tongue cleaner|જીભ સાફ કરવાની પટ્ટી'),
  ('Skin Care','ત્વચાની સંભાળ','Face wash|ફેસ વૉશ;Face cream|ફેસ ક્રીમ;Body lotion|બોડી લોશન;Talcum powder|ટેલ્કમ પાવડર;Sunscreen|સનસ્ક્રીન;Lip balm|લિપ બામ'),
  ('Shaving & Grooming','શેવિંગ અને ગ્રૂમિંગ','Razors|રેઝર;Shaving cream|શેવિંગ ક્રીમ;After-shave|આફ્ટર શેવ;Deodorant|ડિઓડરન્ટ;Perfume|પરફ્યુમ'),
  ('Feminine Hygiene','મહિલા સ્વચ્છતા','Sanitary pads|સેનિટરી પેડ;Intimate wash|ઇન્ટિમેટ વૉશ'),
  ('Baby Food','બાળકોનો ખોરાક','Cerelac|સેરેલેક;Nestum|નેસ્ટમ;Baby biscuits|બેબી બિસ્કિટ'),
  ('Baby Hygiene','બાળકોની સંભાળ','Diapers|ડાયપર;Baby wipes|બેબી વાઇપ્સ;Baby soap|બેબી સાબુ;Baby oil|બેબી તેલ;Baby powder|બેબી પાવડર;Baby shampoo|બેબી શેમ્પૂ;Feeding bottles|ફીડિંગ બોટલ'),
  ('Care Others','અન્ય સંભાળ','Cotton|રૂ;Earbuds|ઈયરબડ;Comb|કાંસકો;Nail cutter|નેઇલ કટર')]),
 ('household','Household, Puja & Stationery','ઘરવપરાશ, પૂજા અને સ્ટેશનરી','🧹',[
  ('Laundry','કપડાંની સફાઈ','Detergent powder|કપડાં ધોવાનો પાવડર;Liquid detergent|લિક્વિડ ડિટર્જન્ટ;Detergent bar|કપડાં ધોવાનો સાબુ;Fabric softener|ફેબ્રિક સોફ્ટનર;Stain remover|ડાઘ દૂર કરનાર'),
  ('Dishwash','વાસણની સફાઈ','Dishwash bar|વાસણ ધોવાનો સાબુ;Dishwash liquid|વાસણ ધોવાનું લિક્વિડ;Scrub pads|સ્ક્રબ પેડ;Steel scrubbers|સ્ટીલ સ્ક્રબર'),
  ('Floor & Toilet Cleaners','ફ્લોર અને ટોઇલેટ ક્લીનર','Floor cleaner|ફ્લોર ક્લીનર;Phenyl|ફિનાઇલ;Toilet cleaner|ટોઇલેટ ક્લીનર;Bathroom cleaner|બાથરૂમ ક્લીનર;Glass cleaner|ગ્લાસ ક્લીનર'),
  ('Pest Control','જીવાત નિયંત્રણ','Mosquito coils|મચ્છર અગરબત્તી;Liquid vaporiser|લિક્વિડ વેપરાઇઝર;Cockroach spray|વંદા મારવાની સ્પ્રે;Naphthalene balls|નેપ્થેલિન ગોળી'),
  ('Disposables','એકવાર વાપરવાની વસ્તુઓ','Tissue paper|ટિશ્યુ પેપર;Garbage bags|કચરાની થેલી;Aluminium foil|એલ્યુમિનિયમ ફોઇલ;Cling film|ક્લિંગ ફિલ્મ;Paper napkins|પેપર નેપકિન;Disposable plates|ડિસ્પોઝેબલ પ્લેટ;Disposable cups|ડિસ્પોઝેબલ કપ'),
  ('Daily Puja','રોજની પૂજા','Agarbatti|અગરબત્તી;Dhoop|ધૂપ;Camphor|કપૂર;Cotton wicks|રૂની વાટ;Ghee diya|ઘીનો દીવો'),
  ('Puja Powders','પૂજાના પાવડર','Kumkum|કંકુ;Puja haldi|પૂજાની હળદર;Sindoor|સિંદૂર;Gulal|ગુલાલ;Chandan|ચંદન'),
  ('Seasonal Items','તહેવારની વસ્તુઓ','Kites|પતંગ;Manja|માંજો;Til-gud|તલ ગોળ;Garba items|ગરબાની વસ્તુઓ;Sama rice|સામો;Diyas|દિવા;Rangoli colours|રંગોળીના રંગ'),
  ('Household Others','અન્ય ઘરવપરાશ','Matchboxes|દીવાસળી;Candles|મીણબત્તી;Batteries|બેટરી;Bulbs|બલ્બ;Puja coconut|પૂજાનું નાળિયેર;Kalawa|નાડાછડી;Gangajal|ગંગાજળ;Pens|પેન;Notebooks|નોટબુક;Glue|ગુંદર;Plastic bags|પ્લાસ્ટિક થેલી')]),
]

CATEGORIES = [('all','All items','બધી વસ્તુઓ','▦')] + [(key,en,gu,icon) for key,en,gu,icon,_ in CATALOG]
SUBCATEGORIES = {key: [(en,gu) for en,gu,_ in groups] for key,_,_,_,groups in CATALOG}
TEMPLATES = [(key, sub_en, sub_gu, en, gu)
             for key,_,_,_,groups in CATALOG
             for sub_en,sub_gu,items in groups
             for en,gu in (pair.split('|') for pair in items.split(';'))]

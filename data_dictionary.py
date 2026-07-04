from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

class Category(Enum):
    PRODUCE = "Produce"
    MEAT = "Meat"
    SEAFOOD = "Seafood"
    DAIRY = "Dairy"
    PANTRY = "Pantry"
    BEVERAGE = "Beverage"
    SNACKS = "Snacks"
    FROZEN = "Frozen"

class Unit(Enum):
    KG = "kg"
    LITER = "L"
    PIECE = "piece"
    GRAM = "g"
    ML = "ml"

@dataclass
class IngredientTranslation:
    en: str
    nl: str
    zh_tw: str
    zh_cn: str

@dataclass
class Ingredient:
    id: str
    translations: IngredientTranslation
    category: Category
    expected_unit: Unit
    default_variant: str
    default_brand_preference: str
    available_variants: List[str]
    tags: List[str]
    excluded_keywords: List[str] = field(default_factory=list)

@dataclass
class SupermarketConfig:
    name: str
    has_api: bool
    fallback_scraper: bool
    budget_level: int # 1 = low, 2 = medium, 3 = high
    base_url: str
    api_endpoints: Dict[str, str]

@dataclass
class AppConfig:
    api_key: str = ""
    ai_provider: str = ""
    ai_model: str = ""

class DataManager:
    """
    Manages data dictionaries and application configurations.
    Designed for dependency injection to avoid global variables.
    """
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self.ingredients = self._init_ingredients()
        self.supermarkets = self._init_supermarkets()

    def _init_ingredients(self) -> Dict[str, Ingredient]:
        return {
            # ================== DAIRY & EGGS ==================
            "milk": Ingredient("milk", IngredientTranslation("Milk", "Melk", "牛奶", "牛奶"), Category.DAIRY, Unit.LITER, "halfvolle melk", "cheapest", ["volle melk", "halfvolle melk", "magere melk"], ["melk", "zuivel", "dairy", "milk"], ["chocolade", "choco", "tablet", "reep", "koek", "koffie", "cups", "poeder", "condens", "gecondenseerde", "geëvaporeerde", "toilet", "papier", "biscuit", "wafel", "katten", "honden", "soja", "soya", "amandel", "haver", "rijst", "kokos", "macadamia", "erwten", "drink"]),
            "high_protein_milk": Ingredient("high_protein_milk", IngredientTranslation("High Protein Milk", "Proteïne Melk", "高蛋白牛奶", "高蛋白牛奶"), Category.DAIRY, Unit.LITER, "proteïne melk", "cheapest", ["proteïne melk", "eiwitrijke melk"], ["melk", "proteine", "eiwit", "zuivel"], ["chocolade", "choco", "reep", "koek", "poeder", "repen", "bar", "snack"]),
            "butter": Ingredient("butter", IngredientTranslation("Butter", "Boter", "奶油", "黄油"), Category.DAIRY, Unit.GRAM, "ongezouten roomboter", "cheapest", ["ongezouten roomboter", "gezouten roomboter", "margarine", "halvarine"], ["boter", "butter", "zuivel"], ["pindakaas", "appel", "chocolade", "koek", "saus", "vloeibaar"]),
            "cheese_gouda": Ingredient("cheese_gouda", IngredientTranslation("Gouda Cheese", "Goudse Kaas", "豪達起司", "高达奶酪"), Category.DAIRY, Unit.GRAM, "jonge kaas", "cheapest", ["jonge kaas", "jong belegen kaas", "oude kaas", "extra belegen"], ["kaas", "cheese", "gouda", "zuivel"], ["soufflé", "saus", "chips", "koek", "snack", "tosti", "salade", "broodje", "pizza"]),
            "mozzarella": Ingredient("mozzarella", IngredientTranslation("Mozzarella", "Mozzarella", "莫札瑞拉起司", "马苏里拉奶酪"), Category.DAIRY, Unit.GRAM, "mozzarella", "cheapest", ["mozzarella", "buffelmozzarella"], ["kaas", "cheese", "mozzarella", "Italiaans"], ["pizza", "salade", "saus", "sticks", "snack"]),
            "feta": Ingredient("feta", IngredientTranslation("Feta Cheese", "Feta", "菲達起司", "菲达奶酪"), Category.DAIRY, Unit.GRAM, "feta", "cheapest", ["feta", "witte kaas"], ["kaas", "cheese", "feta", "Grieks"], ["salade", "pizza", "snack", "broodje"]),
            "parmesan": Ingredient("parmesan", IngredientTranslation("Parmesan", "Parmezaanse Kaas", "帕瑪森起司", "帕马森奶酪"), Category.DAIRY, Unit.GRAM, "parmigiano reggiano", "cheapest", ["parmigiano reggiano", "grana padano", "strooikaas"], ["kaas", "cheese", "parmezaan", "Italiaans"], ["saus", "salade", "pizza", "snack"]),
            "yogurt": Ingredient("yogurt", IngredientTranslation("Yogurt", "Yoghurt", "優格", "酸奶"), Category.DAIRY, Unit.LITER, "volle yoghurt", "cheapest", ["volle yoghurt", "magere yoghurt", "Griekse yoghurt", "plantaardige yoghurt"], ["yoghurt", "yogurt", "zuivel"], ["ijs", "drink", "gums", "snoep", "koek", "saus", "chocolade"]),
            "greek_yogurt": Ingredient("greek_yogurt", IngredientTranslation("Greek Yogurt", "Griekse Yoghurt", "希臘優格", "希腊酸奶"), Category.DAIRY, Unit.LITER, "Griekse yoghurt 10%", "cheapest", ["Griekse yoghurt 10%", "Griekse yoghurt 0%", "Griekse stijl yoghurt"], ["yoghurt", "grieks", "zuivel"], ["ijs", "drink", "gums", "snoep", "koek", "saus", "chocolade"]),
            "quark": Ingredient("quark", IngredientTranslation("Quark", "Kwark", "夸克起司", "夸克奶酪"), Category.DAIRY, Unit.GRAM, "magere kwark", "cheapest", ["magere kwark", "volle kwark", "Franse kwark"], ["kwark", "zuivel", "proteine"], ["ijs", "drink", "gums", "snoep", "koek", "saus", "chocolade"]),
            "high_protein_yogurt": Ingredient("high_protein_yogurt", IngredientTranslation("High Protein Yogurt", "Proteïne Yoghurt", "高蛋白優格", "高蛋白酸奶"), Category.DAIRY, Unit.GRAM, "proteïne yoghurt", "cheapest", ["proteïne yoghurt", "skyr", "proteïne kwark"], ["yoghurt", "proteine", "skyr", "eiwit", "zuivel"], ["ijs", "drink", "gums", "snoep", "koek", "saus", "chocolade"]),
            "egg": Ingredient("egg", IngredientTranslation("Eggs", "Eieren", "雞蛋", "鸡蛋"), Category.DAIRY, Unit.PIECE, "scharreleieren", "cheapest", ["scharreleieren", "vrije-uitloopeieren", "biologische eieren", "omega-3 eieren"], ["ei", "eieren", "eggs", "zuivel"], ["chocolade", "choco", "paas", "salade", "koek", "vlees", "saus", "eierkoek", "verrassing", "spek", "mayonaise", "pasta", "bami", "nasi", "spaghetti", "macaroni", "noedels", "mie", "kruiden"]),
            "cream": Ingredient("cream", IngredientTranslation("Cream", "Slagroom", "鮮奶油", "奶油"), Category.DAIRY, Unit.ML, "slagroom", "cheapest", ["slagroom", "kookroom", "creme fraiche", "zure room"], ["room", "slagroom", "cream", "zuivel"], ["ijs", "chocolade", "koek", "taart", "soes"]),
            "oat_milk": Ingredient("oat_milk", IngredientTranslation("Oat Milk", "Havermelk", "燕麥奶", "燕麦奶"), Category.DAIRY, Unit.LITER, "haverdrank", "oatly", ["haverdrank", "barista haverdrank"], ["havermelk", "plantaardig", "vegan", "melk"], ["chocolade", "koek", "ijs"]),

            # ================== PRODUCE (VEGETABLES) ==================
            "potato": Ingredient("potato", IngredientTranslation("Potato", "Aardappel", "馬鈴薯", "土豆"), Category.PRODUCE, Unit.KG, "kruimige aardappelen", "cheapest", ["kruimige aardappelen", "vastkokende aardappelen", "krieltjes", "zoete aardappel"], ["aardappel", "potato", "groente", "vegetables"], ["chips", "puree", "salade", "kroket", "schijfjes", "partjes", "friet", "patat"]),
            "sweet_potato": Ingredient("sweet_potato", IngredientTranslation("Sweet Potato", "Zoete Aardappel", "地瓜", "红薯"), Category.PRODUCE, Unit.KG, "zoete aardappel", "cheapest", ["zoete aardappel"], ["zoete aardappel", "groente", "vegetables"], ["chips", "puree", "friet", "patat", "salade"]),
            "onion": Ingredient("onion", IngredientTranslation("Onion", "Ui", "洋蔥", "洋葱"), Category.PRODUCE, Unit.KG, "gele uien", "cheapest", ["gele uien", "rode uien", "sjalotten", "bosui"], ["ui", "uien", "onion", "groente"], ["poeder", "ringen", "soep", "saus", "chips", "kruiden"]),
            "garlic": Ingredient("garlic", IngredientTranslation("Garlic", "Knoflook", "大蒜", "大蒜"), Category.PRODUCE, Unit.PIECE, "knoflook", "cheapest", ["knoflook", "verse knoflook", "knoflookpoeder"], ["knoflook", "garlic", "groente"], ["poeder", "saus", "brood", "boter", "kruiden"]),
            "tomato": Ingredient("tomato", IngredientTranslation("Tomato", "Tomaat", "番茄", "番茄"), Category.PRODUCE, Unit.KG, "trostomaten", "cheapest", ["trostomaten", "cherrytomaten", "vleestomaten", "snoeptomaatjes"], ["tomaat", "tomato", "groente"], ["ketchup", "saus", "puree", "soep", "sap", "tapenade", "salade", "pasta"]),
            "cucumber": Ingredient("cucumber", IngredientTranslation("Cucumber", "Komkommer", "黃瓜", "黄瓜"), Category.PRODUCE, Unit.PIECE, "komkommer", "cheapest", ["komkommer", "biologische komkommer", "snackkomkommer"], ["komkommer", "cucumber", "groente"], ["salade", "zuur", "relish", "saus"]),
            "bell_pepper": Ingredient("bell_pepper", IngredientTranslation("Bell Pepper", "Paprika", "甜椒", "甜椒"), Category.PRODUCE, Unit.PIECE, "rode paprika", "cheapest", ["rode paprika", "gele paprika", "groene paprika", "paprika mix", "puntpaprika"], ["paprika", "bell pepper", "groente"], ["chips", "saus", "salade", "kruiden", "poeder"]),
            "carrot": Ingredient("carrot", IngredientTranslation("Carrot", "Wortel", "胡蘿蔔", "胡萝卜"), Category.PRODUCE, Unit.KG, "waspeen", "cheapest", ["waspeen", "winterpeen", "bospeen", "snackworteltjes"], ["wortel", "carrot", "groente"], ["sap", "salade", "cake", "puree", "mix"]),
            "broccoli": Ingredient("broccoli", IngredientTranslation("Broccoli", "Broccoli", "花椰菜", "西兰花"), Category.PRODUCE, Unit.PIECE, "broccoli", "cheapest", ["broccoli", "biologische broccoli", "bimi"], ["broccoli", "groente"], ["soep", "rijst", "mix", "salade", "saus"]),
            "cauliflower": Ingredient("cauliflower", IngredientTranslation("Cauliflower", "Bloemkool", "白花椰菜", "菜花"), Category.PRODUCE, Unit.PIECE, "bloemkool", "cheapest", ["bloemkool", "bloemkoolroosjes"], ["bloemkool", "groente", "kool"], ["soep", "rijst", "mix", "salade", "saus"]),
            "spinach": Ingredient("spinach", IngredientTranslation("Spinach", "Spinazie", "菠菜", "菠菜"), Category.PRODUCE, Unit.GRAM, "verse spinazie", "cheapest", ["verse spinazie", "wilde spinazie", "diepvries spinazie", "babyspinazie"], ["spinazie", "spinach", "groente"], ["a la creme", "pizza", "soep", "salade", "saus", "mix", "smoothie"]),
            "lettuce": Ingredient("lettuce", IngredientTranslation("Lettuce", "Sla", "生菜", "生菜"), Category.PRODUCE, Unit.PIECE, "ijsbergsla", "cheapest", ["ijsbergsla", "kropsla", "romaine sla", "rucola", "veldsla"], ["sla", "lettuce", "groente"], ["mix", "salade", "pakket"]),
            "mushroom": Ingredient("mushroom", IngredientTranslation("Mushroom", "Champignon", "蘑菇", "蘑菇"), Category.PRODUCE, Unit.GRAM, "witte champignons", "cheapest", ["witte champignons", "kastanjechampignons", "portobello", "shiitake"], ["champignon", "mushroom", "groente", "paddenstoel"], ["soep", "saus", "salade", "pizza", "mix"]),
            "mushroom_shiitake": Ingredient("mushroom_shiitake", IngredientTranslation("Shiitake", "Shiitake", "香菇", "香菇"), Category.PRODUCE, Unit.GRAM, "verse shiitake", "cheapest", ["verse shiitake", "gedroogde shiitake"], ["shiitake", "mushroom", "paddenstoel", "groente"], ["soep", "saus", "mix"]),
            "mushroom_oyster": Ingredient("mushroom_oyster", IngredientTranslation("Oyster Mushroom", "Oesterzwam", "杏鮑菇/蠔菇", "平菇/蚝菇"), Category.PRODUCE, Unit.GRAM, "oesterzwammen", "cheapest", ["oesterzwammen", "koningsoesterzwam"], ["oesterzwam", "mushroom", "paddenstoel", "groente"], ["soep", "saus", "mix"]),
            "mushroom_chestnut": Ingredient("mushroom_chestnut", IngredientTranslation("Chestnut Mushroom", "Kastanjechampignon", "栗蘑", "栗蘑"), Category.PRODUCE, Unit.GRAM, "kastanjechampignons", "cheapest", ["kastanjechampignons", "biologische kastanjechampignons"], ["champignon", "kastanje", "mushroom", "paddenstoel"], ["soep", "saus", "mix", "salade"]),
            "mushroom_shimeji": Ingredient("mushroom_shimeji", IngredientTranslation("Shimeji Mushroom", "Beukenzwam", "鴻禧菇", "鸿禧菇"), Category.PRODUCE, Unit.GRAM, "beukenzwam", "cheapest", ["beukenzwam", "witte beukenzwam", "bruine beukenzwam"], ["beukenzwam", "shimeji", "mushroom", "paddenstoel", "groente"], ["soep", "saus", "mix"]),
            "mushroom_portobello": Ingredient("mushroom_portobello", IngredientTranslation("Portobello", "Portobello", "波特菇", "大褐菇"), Category.PRODUCE, Unit.PIECE, "portobello", "cheapest", ["portobello"], ["portobello", "mushroom", "paddenstoel", "groente"], ["soep", "saus", "mix", "burger"]),
            "zucchini": Ingredient("zucchini", IngredientTranslation("Zucchini", "Courgette", "櫛瓜", "西葫芦"), Category.PRODUCE, Unit.PIECE, "courgette", "cheapest", ["courgette", "gele courgette"], ["courgette", "zucchini", "groente"], ["soep", "mix", "salade", "saus", "spaghetti"]),
            "eggplant": Ingredient("eggplant", IngredientTranslation("Eggplant", "Aubergine", "茄子", "茄子"), Category.PRODUCE, Unit.PIECE, "aubergine", "cheapest", ["aubergine", "graffiti aubergine"], ["aubergine", "eggplant", "groente"], ["soep", "mix", "salade", "saus", "dip"]),
            "green_beans": Ingredient("green_beans", IngredientTranslation("Green Beans", "Sperziebonen", "四季豆", "四季豆"), Category.PRODUCE, Unit.GRAM, "sperziebonen", "cheapest", ["sperziebonen", "haricots verts", "snijbonen"], ["sperziebonen", "bonen", "groente"], ["mix", "soep", "salade"]),
            "leek": Ingredient("leek", IngredientTranslation("Leek", "Prei", "韭蔥", "韭葱"), Category.PRODUCE, Unit.PIECE, "prei", "cheapest", ["prei", "gesneden prei"], ["prei", "leek", "groente"], ["soep", "mix", "salade"]),
            "celery": Ingredient("celery", IngredientTranslation("Celery", "Bleekselderij", "西洋芹", "芹菜"), Category.PRODUCE, Unit.PIECE, "bleekselderij", "cheapest", ["bleekselderij", "knolselderij"], ["bleekselderij", "selderij", "groente"], ["soep", "salade", "sap", "mix"]),
            "brussels_sprouts": Ingredient("brussels_sprouts", IngredientTranslation("Brussels Sprouts", "Spruitjes", "抱子甘藍", "抱子甘蓝"), Category.PRODUCE, Unit.GRAM, "spruitjes", "cheapest", ["spruitjes", "schoongemaakte spruitjes"], ["spruitjes", "groente", "kool"], ["mix", "salade"]),
            "kale": Ingredient("kale", IngredientTranslation("Kale", "Boerenkool", "羽衣甘藍", "羽衣甘蓝"), Category.PRODUCE, Unit.GRAM, "gesneden boerenkool", "cheapest", ["gesneden boerenkool", "hele boerenkool"], ["boerenkool", "kale", "groente", "kool"], ["mix", "salade", "smoothie"]),
            "endive": Ingredient("endive", IngredientTranslation("Endive", "Andijvie", "菊苣", "苦苣"), Category.PRODUCE, Unit.GRAM, "gesneden andijvie", "cheapest", ["gesneden andijvie", "krop andijvie"], ["andijvie", "groente", "stamppot"], ["mix", "salade"]),

            # ================== PRODUCE (FRUITS) ==================
            "apple": Ingredient("apple", IngredientTranslation("Apple", "Appel", "蘋果", "苹果"), Category.PRODUCE, Unit.KG, "elstar", "cheapest", ["elstar", "jonagold", "granny smith", "pink lady", "royal gala"], ["appel", "fruit", "apple"], ["sap", "moes", "koek", "taart", "stroop", "azijn", "chips"]),
            "banana": Ingredient("banana", IngredientTranslation("Banana", "Banaan", "香蕉", "香蕉"), Category.PRODUCE, Unit.KG, "bananen", "cheapest", ["bananen", "biologische bananen", "fairtrade bananen"], ["banaan", "banana", "fruit"], ["sap", "koek", "snoep", "ijs", "chips"]),
            "orange": Ingredient("orange", IngredientTranslation("Orange", "Sinaasappel", "柳橙", "橙子"), Category.PRODUCE, Unit.KG, "perssinaasappelen", "cheapest", ["perssinaasappelen", "handsinaasappelen", "bloedsinaasappel"], ["sinaasappel", "orange", "fruit", "citrus"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop"]),
            "lemon": Ingredient("lemon", IngredientTranslation("Lemon", "Citroen", "檸檬", "柠檬"), Category.PRODUCE, Unit.PIECE, "citroen", "cheapest", ["citroen", "biologische citroen"], ["citroen", "lemon", "fruit", "citrus"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "azijn"]),
            "lime": Ingredient("lime", IngredientTranslation("Lime", "Limoen", "萊姆", "青柠"), Category.PRODUCE, Unit.PIECE, "limoen", "cheapest", ["limoen"], ["limoen", "lime", "fruit", "citrus"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "azijn"]),
            "strawberry": Ingredient("strawberry", IngredientTranslation("Strawberry", "Aardbei", "草莓", "草莓"), Category.PRODUCE, Unit.GRAM, "aardbeien", "cheapest", ["aardbeien", "Hollandse aardbeien"], ["aardbei", "strawberry", "fruit", "zomerfruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "saus", "jam"]),
            "grape": Ingredient("grape", IngredientTranslation("Grape", "Druif", "葡萄", "葡萄"), Category.PRODUCE, Unit.GRAM, "witte druiven pitloos", "cheapest", ["witte druiven pitloos", "rode druiven pitloos", "blauwe druiven"], ["druif", "druiven", "grape", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "rozijn"]),
            "avocado": Ingredient("avocado", IngredientTranslation("Avocado", "Avocado", "酪梨", "牛油果"), Category.PRODUCE, Unit.PIECE, "avocado eetrijp", "cheapest", ["avocado eetrijp", "avocado", "hass avocado"], ["avocado", "groente", "fruit"], ["saus", "salade", "dip", "guacamole", "olie"]),
            "mango": Ingredient("mango", IngredientTranslation("Mango", "Mango", "芒果", "芒果"), Category.PRODUCE, Unit.PIECE, "mango eetrijp", "cheapest", ["mango eetrijp", "mango"], ["mango", "fruit", "tropisch"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "saus", "chutney"]),
            "pineapple": Ingredient("pineapple", IngredientTranslation("Pineapple", "Ananas", "鳳梨", "菠萝"), Category.PRODUCE, Unit.PIECE, "ananas", "cheapest", ["ananas", "stukjes ananas"], ["ananas", "fruit", "tropisch"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "saus"]),
            "kiwi": Ingredient("kiwi", IngredientTranslation("Kiwi", "Kiwi", "奇異果", "猕猴桃"), Category.PRODUCE, Unit.PIECE, "kiwi groen", "zespri", ["kiwi groen", "kiwi gold"], ["kiwi", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop"]),
            "peach": Ingredient("peach", IngredientTranslation("Peach", "Perzik", "桃子", "桃子"), Category.PRODUCE, Unit.GRAM, "wilde perzik", "cheapest", ["wilde perzik", "gele perzik", "nectarine"], ["perzik", "fruit", "zomerfruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "jam"]),
            "plum": Ingredient("plum", IngredientTranslation("Plum", "Pruim", "李子", "李子"), Category.PRODUCE, Unit.GRAM, "pruimen", "cheapest", ["pruimen", "rode pruimen"], ["pruim", "fruit", "zomerfruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "jam"]),
            "cherry": Ingredient("cherry", IngredientTranslation("Cherry", "Kersen", "櫻桃", "樱桃"), Category.PRODUCE, Unit.GRAM, "kersen", "cheapest", ["kersen"], ["kersen", "fruit", "zomerfruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "jam", "saus"]),
            "raspberry": Ingredient("raspberry", IngredientTranslation("Raspberry", "Framboos", "覆盆子", "树莓"), Category.PRODUCE, Unit.GRAM, "frambozen", "cheapest", ["frambozen", "diepvries frambozen"], ["frambozen", "fruit", "zomerfruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "jam", "saus"]),
            "blueberry": Ingredient("blueberry", IngredientTranslation("Blueberry", "Blauwe Bes", "藍莓", "蓝莓"), Category.PRODUCE, Unit.GRAM, "blauwe bessen", "cheapest", ["blauwe bessen", "diepvries blauwe bessen"], ["blauwe bessen", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "jam", "saus"]),
            "blackberry": Ingredient("blackberry", IngredientTranslation("Blackberry", "Braam", "黑莓", "黑莓"), Category.PRODUCE, Unit.GRAM, "bramen", "cheapest", ["bramen", "diepvries bramen"], ["bramen", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "jam", "saus"]),
            "watermelon": Ingredient("watermelon", IngredientTranslation("Watermelon", "Watermeloen", "西瓜", "西瓜"), Category.PRODUCE, Unit.PIECE, "watermeloen", "cheapest", ["watermeloen", "pitloze watermeloen", "stukken watermeloen"], ["watermeloen", "meloen", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "salade"]),
            "melon": Ingredient("melon", IngredientTranslation("Melon", "Meloen", "哈密瓜", "甜瓜"), Category.PRODUCE, Unit.PIECE, "galiameloen", "cheapest", ["galiameloen", "cantaloupe", "honingmeloen"], ["meloen", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "salade"]),
            "pomegranate": Ingredient("pomegranate", IngredientTranslation("Pomegranate", "Granaatappel", "石榴", "石榴"), Category.PRODUCE, Unit.PIECE, "granaatappel", "cheapest", ["granaatappel", "granaatappelpitjes"], ["granaatappel", "fruit"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "salade"]),
            "passion_fruit": Ingredient("passion_fruit", IngredientTranslation("Passion Fruit", "Passievrucht", "百香果", "百香果"), Category.PRODUCE, Unit.PIECE, "passievrucht", "cheapest", ["passievrucht"], ["passievrucht", "fruit", "tropisch"], ["sap", "koek", "snoep", "ijs", "limonade", "siroop", "saus"]),

            # ================== MEAT ==================
            "ground_beef": Ingredient("ground_beef", IngredientTranslation("Ground Beef", "Rundergehakt", "牛絞肉", "牛肉馅"), Category.MEAT, Unit.KG, "mager rundergehakt", "cheapest", ["mager rundergehakt", "rundergehakt", "half om half gehakt", "rundergehakt extra mager"], ["gehakt", "rundvlees", "beef", "meat", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger"]),
            "beef_steak": Ingredient("beef_steak", IngredientTranslation("Beef Steak", "Biefstuk", "牛排", "牛排"), Category.MEAT, Unit.KG, "kogelbiefstuk", "cheapest", ["kogelbiefstuk", "haasbiefstuk", "runderbiefstuk", "ribeye", "entrecote"], ["biefstuk", "rundvlees", "beef", "meat", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger", "worst"]),
            "beef_stew": Ingredient("beef_stew", IngredientTranslation("Stewing Beef", "Riblap/Sukadelap", "燉牛肉", "炖牛肉"), Category.MEAT, Unit.KG, "runder riblap", "cheapest", ["runder riblap", "sukadelap", "runderpoulet", "stoofvlees"], ["stoofvlees", "riblap", "sukade", "rundvlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger"]),
            "beef_burger": Ingredient("beef_burger", IngredientTranslation("Beef Burger", "Hamburger", "牛肉漢堡排", "牛肉汉堡饼"), Category.MEAT, Unit.PIECE, "runderhamburger", "cheapest", ["runderhamburger", "angus burger", "verse worst"], ["hamburger", "burger", "rundvlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "broodje"]),
            
            "chicken_breast": Ingredient("chicken_breast", IngredientTranslation("Chicken Breast", "Kipfilet", "雞胸肉", "鸡胸肉"), Category.MEAT, Unit.KG, "kipfilet", "cheapest", ["kipfilet", "scharrel kipfilet", "biologische kipfilet", "kiphaasjes"], ["kip", "kipfilet", "chicken", "meat", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger", "worst", "beleg", "plakjes"]),
            "chicken_thigh": Ingredient("chicken_thigh", IngredientTranslation("Chicken Thigh", "Kippendij", "雞腿肉", "鸡腿肉"), Category.MEAT, Unit.KG, "kippendijfilet", "cheapest", ["kippendijfilet", "kippendijen met bot", "scharrel kippendijfilet"], ["kip", "kippendij", "chicken", "meat"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger"]),
            "chicken_wing": Ingredient("chicken_wing", IngredientTranslation("Chicken Wings", "Kippenvleugels", "雞翅", "鸡翅"), Category.MEAT, Unit.KG, "kippenvleugels", "cheapest", ["kippenvleugels", "borrelhapjes", "kipkluifjes"], ["kip", "kippenvleugels", "chicken", "wings", "snack"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger"]),
            "chicken_drumstick": Ingredient("chicken_drumstick", IngredientTranslation("Chicken Drumsticks", "Kippenbouten/Drumsticks", "棒棒腿", "鸡小腿"), Category.MEAT, Unit.KG, "drumsticks", "cheapest", ["drumsticks", "kippenbouten"], ["kip", "drumsticks", "chicken", "bouten"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger"]),
            "whole_chicken": Ingredient("whole_chicken", IngredientTranslation("Whole Chicken", "Hele Kip", "全雞", "全鸡"), Category.MEAT, Unit.PIECE, "hele scharrelkip", "cheapest", ["hele scharrelkip", "grillkip", "braadkuiken"], ["kip", "hele kip", "chicken", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "plantaardig", "bouillon", "vleesvervanger"]),
            
            "pork_chop": Ingredient("pork_chop", IngredientTranslation("Pork Chop", "Karbonade", "豬排", "猪排"), Category.MEAT, Unit.KG, "schouderkarbonade", "cheapest", ["schouderkarbonade", "haaskarbonade", "ribkarbonade", "halskarbonade"], ["karbonade", "varkensvlees", "pork", "meat", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger"]),
            "pork_tenderloin": Ingredient("pork_tenderloin", IngredientTranslation("Pork Tenderloin", "Varkenshaas", "豬里肌", "猪里脊"), Category.MEAT, Unit.KG, "varkenshaas", "cheapest", ["varkenshaas", "varkensfilet"], ["varkenshaas", "varkensvlees", "pork", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "salade"]),
            "pork_belly": Ingredient("pork_belly", IngredientTranslation("Pork Belly", "Buikspek", "豬五花", "五花肉"), Category.MEAT, Unit.KG, "speklappen", "cheapest", ["speklappen", "gemarineerde speklappen", "buikspek stuk"], ["speklappen", "buikspek", "varkensvlees", "pork"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "snack"]),
            "bacon": Ingredient("bacon", IngredientTranslation("Bacon", "Spek", "培根", "培根"), Category.MEAT, Unit.GRAM, "ontbijtspek", "cheapest", ["ontbijtspek", "spekreepjes", "pancetta", "katenspek"], ["spek", "bacon", "varkensvlees", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "snack", "chips"]),
            "sausage": Ingredient("sausage", IngredientTranslation("Sausage", "Worst", "香腸", "香肠"), Category.MEAT, Unit.KG, "braadworst", "cheapest", ["braadworst", "rookworst", "knakworst", "verse worst", "saucijzen"], ["worst", "sausage", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "broodje", "soep"]),
            
            "lamb_chop": Ingredient("lamb_chop", IngredientTranslation("Lamb Chop", "Lamskotelet", "羊排", "羊排"), Category.MEAT, Unit.KG, "lamskotelet", "cheapest", ["lamskotelet", "lamsrack"], ["lam", "lamsvlees", "lamb", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger"]),
            "minced_mixed": Ingredient("minced_mixed", IngredientTranslation("Mixed Minced Meat", "Half om Half Gehakt", "豬牛絞肉", "猪牛混合肉馅"), Category.MEAT, Unit.KG, "half om half gehakt", "cheapest", ["half om half gehakt"], ["gehakt", "varkensvlees", "rundvlees", "meat"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "mix", "saus"]),
            "minced_pork": Ingredient("minced_pork", IngredientTranslation("Minced Pork", "Varkensgehakt", "豬絞肉", "猪肉馅"), Category.MEAT, Unit.KG, "varkensgehakt", "cheapest", ["varkensgehakt", "gekruid varkensgehakt"], ["gehakt", "varkensvlees", "pork", "meat"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "mix"]),
            "minced_chicken": Ingredient("minced_chicken", IngredientTranslation("Minced Chicken", "Kipgehakt", "雞絞肉", "鸡肉馅"), Category.MEAT, Unit.KG, "kipgehakt", "cheapest", ["kipgehakt", "gehakt van kip"], ["gehakt", "kip", "chicken", "meat"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "mix"]),
            "spareribs": Ingredient("spareribs", IngredientTranslation("Spare Ribs", "Spareribs", "豬肋排", "猪肋排"), Category.MEAT, Unit.KG, "spareribs naturel", "cheapest", ["spareribs naturel", "gemarineerde spareribs"], ["spareribs", "ribben", "varkensvlees", "pork", "vlees"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "snack"]),
            "veal": Ingredient("veal", IngredientTranslation("Veal", "Kalfsvlees", "小牛肉", "小牛肉"), Category.MEAT, Unit.KG, "kalfsoester", "cheapest", ["kalfsoester", "kalfsschnitzel"], ["kalf", "kalfsvlees", "veal", "meat"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger"]),
            "turkey_breast": Ingredient("turkey_breast", IngredientTranslation("Turkey Breast", "Kalkoenfilet", "火雞胸肉", "火鸡胸肉"), Category.MEAT, Unit.KG, "kalkoenfilet", "cheapest", ["kalkoenfilet", "kalkoenschnitzel"], ["kalkoen", "turkey", "meat", "gevogelte"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger", "salade"]),
            "duck_breast": Ingredient("duck_breast", IngredientTranslation("Duck Breast", "Eendenborst", "鴨胸肉", "鸭胸肉"), Category.MEAT, Unit.KG, "eendenborstfilet", "cheapest", ["eendenborstfilet", "tamme eendenborst"], ["eend", "eendenborst", "duck", "meat"], ["vega", "vegan", "vegetarisch", "kruiden", "saus", "vleesvervanger"]),
            "salami": Ingredient("salami", IngredientTranslation("Salami", "Salami", "義大利臘腸", "萨拉米香肠"), Category.MEAT, Unit.GRAM, "salami", "cheapest", ["salami", "cervelaat", "snijworst"], ["salami", "vleeswaren", "broodbeleg", "vlees"], ["vega", "vegan", "vegetarisch", "pizza", "snack", "broodje"]),
            "ham": Ingredient("ham", IngredientTranslation("Ham", "Ham", "火腿", "火腿"), Category.MEAT, Unit.GRAM, "achterham", "cheapest", ["achterham", "schouderham", "beenham", "parmaham"], ["ham", "vleeswaren", "broodbeleg", "varkensvlees"], ["vega", "vegan", "vegetarisch", "pizza", "snack", "broodje", "salade", "kaas", "chips"]),

            # ================== SEAFOOD ==================
            "salmon": Ingredient("salmon", IngredientTranslation("Salmon", "Zalm", "鮭魚", "三文鱼"), Category.SEAFOOD, Unit.KG, "zalmfilet", "cheapest", ["zalmfilet", "zalmmoot", "wilde zalm"], ["zalm", "vis", "salmon", "fish", "vers"], ["salade", "saus", "snack", "pizza", "soep", "kruiden", "pasta"]),
            "smoked_salmon": Ingredient("smoked_salmon", IngredientTranslation("Smoked Salmon", "Gerookte Zalm", "燻鮭魚", "烟熏三文鱼"), Category.SEAFOOD, Unit.GRAM, "gerookte zalm", "cheapest", ["gerookte zalm", "wilde gerookte zalm"], ["zalm", "gerookt", "vis", "broodbeleg"], ["salade", "saus", "snack", "pizza", "soep", "kruiden"]),
            "cod": Ingredient("cod", IngredientTranslation("Cod", "Kabeljauw", "鱈魚", "鳕鱼"), Category.SEAFOOD, Unit.KG, "kabeljauwfilet", "cheapest", ["kabeljauwfilet", "kabeljauwhaasje", "kibbeling", "lekkerbekje"], ["kabeljauw", "vis", "witvis", "fish"], ["salade", "saus", "snack", "pizza", "soep", "kruiden", "kibbeling"]),
            "tuna": Ingredient("tuna", IngredientTranslation("Tuna", "Tonijn", "鮪魚", "金枪鱼"), Category.SEAFOOD, Unit.GRAM, "tonijnstukken in water", "princes", ["tonijnstukken in water", "tonijn in olie", "verse tonijnsteak"], ["tonijn", "vis", "blikvis", "fish"], ["salade", "saus", "snack", "pizza", "soep", "kruiden", "pasta"]),
            "shrimp": Ingredient("shrimp", IngredientTranslation("Shrimp", "Garnalen", "蝦子", "虾"), Category.SEAFOOD, Unit.GRAM, "roze garnalen", "cheapest", ["roze garnalen", "wokgarnalen", "grote garnalen", "gamba's"], ["garnalen", "vis", "shrimp", "seafood"], ["salade", "saus", "snack", "pizza", "soep", "kruiden", "kroepoek"]),
            "mussels": Ingredient("mussels", IngredientTranslation("Mussels", "Mosselen", "淡菜/貽貝", "贻贝"), Category.SEAFOOD, Unit.KG, "mosselen", "cheapest", ["mosselen", "gekookte mosselen"], ["mosselen", "schelpdieren", "seafood", "vis"], ["salade", "saus", "snack", "pizza", "soep", "kruiden"]),
            "herring": Ingredient("herring", IngredientTranslation("Herring", "Haring", "鯡魚", "鲱鱼"), Category.SEAFOOD, Unit.PIECE, "Hollandse nieuwe", "cheapest", ["Hollandse nieuwe", "maatjesharing", "zure haring"], ["haring", "vis", "Hollands"], ["salade", "saus", "snack", "pizza", "soep", "kruiden", "salade"]),
            "mackerel": Ingredient("mackerel", IngredientTranslation("Mackerel", "Makreel", "鯖魚", "鲭鱼"), Category.SEAFOOD, Unit.GRAM, "gestoomde makreel", "cheapest", ["gestoomde makreel", "gerookte makreel", "makreelfilet"], ["makreel", "vis", "gerookt"], ["salade", "saus", "snack", "pizza", "soep", "kruiden"]),
            "squid": Ingredient("squid", IngredientTranslation("Squid", "Inktvis", "魷魚", "鱿鱼"), Category.SEAFOOD, Unit.GRAM, "inktvisringen", "cheapest", ["inktvisringen", "calamaris", "hele inktvis"], ["inktvis", "calamaris", "seafood", "vis"], ["salade", "saus", "snack", "pizza", "soep", "kruiden", "ringen"]),
            "fish_fingers": Ingredient("fish_fingers", IngredientTranslation("Fish Fingers", "Vissticks", "炸魚條", "炸鱼条"), Category.FROZEN, Unit.GRAM, "vissticks", "iglo", ["vissticks", "omega-3 vissticks"], ["vissticks", "vis", "diepvries", "snack"], ["saus"]),

            # ================== PANTRY ==================
            "rice": Ingredient("rice", IngredientTranslation("Rice", "Rijst", "米", "米"), Category.PANTRY, Unit.KG, "witte rijst", "cheapest", ["witte rijst", "zilvervliesrijst", "basmati rijst", "pandan rijst", "sushirijst", "risottorijst"], ["rijst", "rice", "grains"], ["zoutje", "koek", "snack", "melk", "olie", "wafel", "azijn", "papier", "saus", "mix", "maaltijd", "pudding"]),
            "pasta": Ingredient("pasta", IngredientTranslation("Pasta", "Pasta", "義大利麵", "意大利面"), Category.PANTRY, Unit.KG, "spaghetti", "cheapest", ["spaghetti", "macaroni", "penne", "fusilli", "tagliatelle", "volkoren pasta"], ["pasta", "spaghetti", "macaroni", "grains"], ["saus", "salade", "mix", "maaltijd", "kruiden"]),
            "bread": Ingredient("bread", IngredientTranslation("Bread", "Brood", "麵包", "面包"), Category.PANTRY, Unit.PIECE, "volkorenbrood", "cheapest", ["volkorenbrood", "witbrood", "tarwebrood", "stokbrood", "afbakbroodjes", "kaiserbroodjes"], ["brood", "bread", "bakery"], ["beleg", "mix", "salade", "kruim", "snack", "chips"]),
            "flour": Ingredient("flour", IngredientTranslation("Flour", "Bloem", "麵粉", "面粉"), Category.PANTRY, Unit.KG, "tarwebloem", "cheapest", ["tarwebloem", "patentbloem", "volkorenmeel", "speltmeel", "zelfrijzend bakmeel"], ["bloem", "meel", "flour", "baking"], ["mix", "koek", "cake", "taart", "brood"]),
            "sugar": Ingredient("sugar", IngredientTranslation("Sugar", "Suiker", "糖", "糖"), Category.PANTRY, Unit.KG, "kristalsuiker", "cheapest", ["kristalsuiker", "poedersuiker", "rietsuiker", "basterdsuiker", "kandij"], ["suiker", "sugar", "baking"], ["vrij", "zero", "vervanger", "koek", "snoep"]),
            "salt": Ingredient("salt", IngredientTranslation("Salt", "Zout", "鹽", "盐"), Category.PANTRY, Unit.GRAM, "keukenzout", "cheapest", ["keukenzout", "zeezout", "Himalayazout"], ["zout", "salt", "spices"], ["chips", "snack", "pinda", "noten", "mix", "kruiden", "vlees", "vis"]),
            "olive_oil": Ingredient("olive_oil", IngredientTranslation("Olive Oil", "Olijfolie", "橄欖油", "橄榄油"), Category.PANTRY, Unit.LITER, "olijfolie extra vierge", "cheapest", ["olijfolie extra vierge", "mild olijfolie", "olijfolie om in te bakken"], ["olijfolie", "olie", "olive oil", "oil"], ["mayonaise", "saus", "dressing", "salade"]),
            "sunflower_oil": Ingredient("sunflower_oil", IngredientTranslation("Sunflower Oil", "Zonnebloemolie", "葵花籽油", "葵花籽油"), Category.PANTRY, Unit.LITER, "zonnebloemolie", "cheapest", ["zonnebloemolie", "frituurolie"], ["zonnebloemolie", "olie", "oil"], ["mayonaise", "saus", "dressing", "salade", "margarine"]),
            "black_pepper": Ingredient("black_pepper", IngredientTranslation("Black Pepper", "Zwarte Peper", "黑胡椒", "黑胡椒"), Category.PANTRY, Unit.GRAM, "zwarte peper gemalen", "cheapest", ["zwarte peper gemalen", "zwarte peperkorrels", "witte peper"], ["peper", "pepper", "spices"], ["saus", "chips", "snack", "mix", "kaas", "worst"]),
            "soy_sauce": Ingredient("soy_sauce", IngredientTranslation("Soy Sauce", "Sojasaus", "醬油", "酱油"), Category.PANTRY, Unit.ML, "sojasaus zout", "kikkoman", ["sojasaus zout", "ketjap manis", "lichte sojasaus"], ["sojasaus", "ketjap", "soy sauce", "sauce", "Aziatisch"], ["marinade", "mix", "snack", "noedels", "chips", "pinda"]),
            "peanut_butter": Ingredient("peanut_butter", IngredientTranslation("Peanut Butter", "Pindakaas", "花生醬", "花生酱"), Category.PANTRY, Unit.GRAM, "pindakaas naturel", "calve", ["pindakaas naturel", "pindakaas met stukjes pinda", "100% pindakaas"], ["pindakaas", "peanut butter", "spreads", "broodbeleg"], ["koek", "snack", "ijs", "snoep", "reep", "chocolade"]),
            "coffee": Ingredient("coffee", IngredientTranslation("Coffee", "Koffie", "咖啡", "咖啡"), Category.PANTRY, Unit.KG, "snelfiltermaling", "douwe egberts", ["snelfiltermaling", "koffiebonen", "koffiepads", "koffiecups", "oploskoffie"], ["koffie", "coffee"], ["filter", "melk", "beker", "koek", "pad", "cup", "ijs", "snoep", "chocolade", "siroop", "likeur"]),
            "tea": Ingredient("tea", IngredientTranslation("Tea", "Thee", "茶", "茶"), Category.PANTRY, Unit.PIECE, "zwarte thee", "pickwick", ["zwarte thee", "groene thee", "rooibos", "munt thee", "kruidenthee"], ["thee", "tea"], ["ijs", "koek", "snoep", "drank", "chocolade", "glas"]),
            "canned_tomato": Ingredient("canned_tomato", IngredientTranslation("Canned Tomato", "Gepelde Tomaten", "番茄罐頭", "番茄罐头"), Category.PANTRY, Unit.GRAM, "gepelde tomaten in blik", "mutti", ["gepelde tomaten in blik", "tomatenblokjes", "gezeefde tomaten (passata)", "tomatenpuree"], ["tomaten blik", "canned tomato", "passata", "puree"], ["soep", "saus", "pasta", "pizza", "mix"]),
            "baked_beans": Ingredient("baked_beans", IngredientTranslation("Baked Beans", "Witte Bonen in Tomatensaus", "烘培豆", "烘培豆"), Category.PANTRY, Unit.GRAM, "witte bonen in tomatensaus", "heinz", ["witte bonen in tomatensaus", "bruine bonen", "kidneybonen", "kikkererwten"], ["bonen", "beans", "blik", "peulvruchten"], ["soep", "saus", "mix", "salade"]),

            # ================== BEVERAGE ==================
            "water": Ingredient("water", IngredientTranslation("Water", "Water", "水", "水"), Category.BEVERAGE, Unit.LITER, "bronwater zonder koolzuur", "bar le duc", ["bronwater zonder koolzuur", "bronwater met koolzuur (bruisend)"], ["water", "drinks", "bronwater"], ["rozen", "kokos", "ijs", "meloen", "koolzuurhoudend", "smaak", "siroop", "limonade"]),
            "orange_juice": Ingredient("orange_juice", IngredientTranslation("Orange Juice", "Sinaasappelsap", "柳橙汁", "橙汁"), Category.BEVERAGE, Unit.LITER, "sinaasappelsap uit concentraat", "appelsientje", ["sinaasappelsap uit concentraat", "verse verse sinaasappelsap (koeling)"], ["sinaasappelsap", "jus d'orange", "juice", "drinks"], ["ijs", "snoep", "koek", "limonade", "siroop"]),
            "apple_juice": Ingredient("apple_juice", IngredientTranslation("Apple Juice", "Appelsap", "蘋果汁", "苹果汁"), Category.BEVERAGE, Unit.LITER, "appelsap helder", "appelsientje", ["appelsap helder", "troebele appelsap"], ["appelsap", "juice", "drinks"], ["ijs", "snoep", "koek", "limonade", "siroop", "azijn"]),
            "chocolate_milk": Ingredient("chocolate_milk", IngredientTranslation("Chocolate Milk", "Chocolademelk", "巧克力牛奶", "巧克力奶"), Category.BEVERAGE, Unit.LITER, "chocomel", "chocomel", ["chocomel", "chocolademelk", "verse chocolademelk", "magere chocolademelk"], ["chocomel", "chocolademelk", "zuivel", "drinks"], ["ijs", "koek", "snoep", "pudding", "vla", "tablet", "reep", "pasta"]),
            "cola": Ingredient("cola", IngredientTranslation("Cola", "Cola", "可樂", "可乐"), Category.BEVERAGE, Unit.LITER, "cola", "coca-cola", ["cola", "cola zero", "cola light"], ["cola", "soda", "drinks", "frisdrank"], ["ijs", "snoep", "koek"]),
            "beer": Ingredient("beer", IngredientTranslation("Beer", "Bier", "啤酒", "啤酒"), Category.BEVERAGE, Unit.LITER, "pilsener", "heineken", ["pilsener", "speciaalbier", "alcoholvrij bier", "radler"], ["bier", "beer", "alcohol", "drinks"], ["worst", "gember", "ginger", "0.0", "alcoholvrij", "azijn", "gist", "saus", "kaas"]),
            "wine_red": Ingredient("wine_red", IngredientTranslation("Red Wine", "Rode Wijn", "紅酒", "红酒"), Category.BEVERAGE, Unit.LITER, "rode wijn", "cheapest", ["rode wijn", "merlot", "cabernet sauvignon", "shiraz", "pinot noir"], ["wijn", "wine", "alcohol", "drinks"], ["azijn", "saus", "alcoholvrij", "kaas", "worst"]),
            "wine_white": Ingredient("wine_white", IngredientTranslation("White Wine", "Witte Wijn", "白酒", "白葡萄酒"), Category.BEVERAGE, Unit.LITER, "witte wijn droog", "cheapest", ["witte wijn droog", "chardonnay", "sauvignon blanc", "pinot grigio", "zoete witte wijn"], ["wijn", "wine", "alcohol", "drinks"], ["azijn", "saus", "alcoholvrij", "kaas", "worst"]),

            # ================== SNACKS ==================
            "potato_chips": Ingredient("potato_chips", IngredientTranslation("Potato Chips", "Chips", "洋芋片", "薯片"), Category.SNACKS, Unit.GRAM, "naturel chips", "lays", ["naturel chips", "paprika chips", "cheese onion chips", "ribbelchips"], ["chips", "snacks", "zoutje"], ["saus", "dip"]),
            "chocolate": Ingredient("chocolate", IngredientTranslation("Chocolate", "Chocolade", "巧克力", "巧克力"), Category.SNACKS, Unit.GRAM, "melkchocolade", "tony chocolonely", ["melkchocolade", "pure chocolade", "witte chocolade", "hazelnootchocolade"], ["chocolade", "chocolate", "candy", "snacks", "snoep"], ["ijs", "koek", "melk", "drink", "saus", "pudding", "vla", "pasta", "hagelslag", "vlokken"]),
            "cookies": Ingredient("cookies", IngredientTranslation("Cookies", "Koekjes", "餅乾", "饼干"), Category.SNACKS, Unit.GRAM, "stroopwafels", "cheapest", ["stroopwafels", "chocolate chip cookies", "speculaas", "roze koeken", "biscuitjes"], ["koek", "koekjes", "cookies", "snacks", "tussendoortje"], ["ijs", "chocolade", "mix"]),
            "nuts": Ingredient("nuts", IngredientTranslation("Nuts", "Noten", "堅果", "坚果"), Category.SNACKS, Unit.GRAM, "gemengde noten ongezouten", "cheapest", ["gemengde noten ongezouten", "gezouten pinda's", "walnoten", "cashewnoten", "amandelen"], ["noten", "nuts", "snacks", "borrelnootjes"], ["chocolade", "koek", "ijs", "saus", "pasta", "olie", "reep", "muesli", "granola"])
        }

    def _init_supermarkets(self) -> Dict[str, SupermarketConfig]:
        return {
            "albert_heijn": SupermarketConfig(
                name="AH",
                has_api=True,
                fallback_scraper=False,
                budget_level=3,
                base_url="https://www.ah.nl",
                api_endpoints={"search": "https://api.ah.nl/search"}
            ),
            "jumbo": SupermarketConfig(
                name="Jumbo",
                has_api=True,
                fallback_scraper=False,
                budget_level=2,
                base_url="https://www.jumbo.com",
                api_endpoints={"search": "https://api.jumbo.com/search"}
            ),
            "dirk": SupermarketConfig(
                name="Dirk",
                has_api=True,
                fallback_scraper=False,
                budget_level=1,
                base_url="https://www.dirk.nl",
                api_endpoints={"search": "https://api.dirk.nl/search"}
            ),
            "aldi": SupermarketConfig(
                name="ALDI",
                has_api=True,
                fallback_scraper=False,
                budget_level=1,
                base_url="https://www.aldi.nl",
                api_endpoints={"search": "https://api.aldi.nl/search"}
            ),
            "lidl": SupermarketConfig(
                name="Lidl (via boodschaapje.nl)",
                has_api=False,
                fallback_scraper=True,
                budget_level=1,
                base_url="https://www.lidl.nl",
                api_endpoints={}
            ),
            "coop": SupermarketConfig(
                name="Coop",
                has_api=True,
                fallback_scraper=False,
                budget_level=2,
                base_url="https://www.coop.nl",
                api_endpoints={"search": "https://api.coop.nl/search"}
            ),
            "hoogvliet": SupermarketConfig(
                name="Hoogvliet",
                has_api=True,
                fallback_scraper=False,
                budget_level=2,
                base_url="https://www.hoogvliet.com",
                api_endpoints={"search": "https://api.hoogvliet.com/search"}
            ),
            "plus": SupermarketConfig(
                name="PLUS",
                has_api=True,
                fallback_scraper=False,
                budget_level=2,
                base_url="https://www.plus.nl",
                api_endpoints={"search": "https://api.plus.nl/search"}
            ),
            "spar": SupermarketConfig(
                name="SPAR",
                has_api=True,
                fallback_scraper=False,
                budget_level=3,
                base_url="https://www.spar.nl",
                api_endpoints={"search": "https://api.spar.nl/search"}
            ),
            "vomar": SupermarketConfig(
                name="Vomar",
                has_api=True,
                fallback_scraper=False,
                budget_level=1,
                base_url="https://www.vomar.nl",
                api_endpoints={"search": "https://api.vomar.nl/search"}
            )
        }
    
    def get_ingredient(self, ingredient_id: str) -> Optional[Ingredient]:
        return self.ingredients.get(ingredient_id)
        
    def get_supermarket(self, supermarket_id: str) -> Optional[SupermarketConfig]:
        return self.supermarkets.get(supermarket_id)

import re
from decimal import Decimal

import spacy

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load('fr_core_news_sm')
        except OSError:
            _nlp = None
    return _nlp


SELL_LEMMAS = {'vendre', 'vente', 'achat', 'acheter', 'prendre', 'donner', 'commander'}
STOCK_LEMMAS = {'stock', 'inventaire', 'disponible', 'reste'}
PRICE_LEMMAS = {'prix', 'tarif', 'coût', 'coufter', 'couter', 'combien', 'payer'}
SUPPLY_LEMMAS = {'approvisionner', 'appro', 'recharger', 'ajouter_stock', 'livrer'}
PRODUCT_LEMMAS = {'ajouter_article', 'nouveau_produit', 'créer', 'créer_produit'}
CLEAR_LEMMAS = {'effacer', 'nettoyer', 'clear', 'reset', 'vider'}


def detect_intent(text):
    """Detect user intent from natural language using spaCy."""
    nlp = _get_nlp()
    if nlp is None:
        return None
    doc = nlp(text.lower().strip())
    lemmas = {token.lemma_ for token in doc}

    if lemmas & SELL_LEMMAS:
        return 'sell'
    if lemmas & STOCK_LEMMAS:
        return 'check_stock'
    if lemmas & PRICE_LEMMAS:
        return 'check_price'
    if lemmas & SUPPLY_LEMMAS:
        return 'supply'
    if lemmas & PRODUCT_LEMMAS:
        return 'add_product'
    if lemmas & CLEAR_LEMMAS:
        return 'clear'
    return None


def has_numeric_intent(text):
    """Check if text likely refers to quantity/amount context (not a product name)."""
    nlp = _get_nlp()
    if nlp is None:
        return None
    doc = nlp(text.lower().strip())
    has_num = any(token.pos_ == 'NUM' for token in doc)
    has_unit = any(token.lemma_ in {'kilogramme', 'litre', 'pièce', 'piece', 'paquet', 'carton'}
                   for token in doc)
    return has_num or has_unit


def extract_entities(text):
    """Extract (products, quantity, mode, amount) from natural language."""
    nlp = _get_nlp()
    if nlp is None:
        return [], None, None, None
    doc = nlp(text.lower().strip())

    qty = None
    mode = None
    amount = None

    for token in doc:
        if token.pos_ == 'NUM':
            val = Decimal(token.text.replace(',', '.'))
            # Check next token for unit
            nxt = doc[token.i + 1] if token.i + 1 < len(doc) else None
            if nxt and nxt.lemma_ in {'kilogramme', 'kilo'}:
                qty = val
                mode = 'kg'
            elif nxt and nxt.lemma_ == 'litre':
                qty = val
                mode = 'l'
            elif nxt and nxt.lemma_ in {'pièce', 'piece'}:
                qty = val
                mode = 'piece'
            elif nxt and nxt.lemma_ in {'paquet', 'carton'}:
                qty = val
                mode = nxt.lemma_
            elif qty is None:
                qty = val

    # Amount: detect "X f" / "X fcfa" / "X francs"
    am = re.search(r'(\d+[\d,.]*)\s*(f(?:cfa)?|francs?|cfa)', text, re.I)
    if am:
        amount = Decimal(am.group(1).replace(',', '.'))
        if qty is None:
            qty = amount
        amount = amount

    # Product name: nouns and proper nouns that aren't stop words or units
    stop = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'je', 'tu', 'il', 'elle',
            'nous', 'vous', 'ils', 'elles', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son',
            'ma', 'ta', 'sa', 'mes', 'tes', 'ses', 'nos', 'vos', 'leur', 'leurs',
            'au', 'aux', 'a', 'et', 'ou', 'en', 'dans', 'sur', 'pour', 'par', 'avec',
            'sans', 'chez', 'entre', 'moi', 'toi', 'lui', 'eux', 'oui', 'non'}
    units = {'kilogramme', 'kilo', 'litre', 'pièce', 'piece', 'paquet', 'carton', 'cartouche',
             'kg', 'l', 'f', 'fcfa', 'franc', 'francs'}
    products = []
    for chunk in doc.noun_chunks:
        words = []
        for t in chunk:
            if t.lemma_ in stop or t.lemma_ in units or t.pos_ == 'NUM' or t.pos_ == 'DET':
                continue
            words.append(t.text)
        if words:
            products.append(' '.join(words))

    # Fallback: take root of sentence
    if not products:
        for token in doc:
            if token.dep_ == 'ROOT' and token.pos_ == 'NOUN' and token.lemma_ not in stop | units:
                products.append(token.text)
                break

    return products, qty, mode, amount

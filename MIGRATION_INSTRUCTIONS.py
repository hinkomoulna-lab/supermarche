"""
INSTRUCTIONS DE MIGRATION
==========================

Après avoir remplacé models.py et views.py, lancez ces commandes dans votre terminal :

    python manage.py makemigrations store
    python manage.py migrate

Cela créera automatiquement les nouvelles colonnes :
  - Sale.sale_date       : date de vente (par défaut = aujourd'hui)
  - Sale.notes           : notes libres sur la vente
  - SaleItem.sale_mode   : 'detail' ou 'paquet'
  - Product.pack_size    : quantité dans un paquet (défaut 1)
  - Product.pack_price   : prix du paquet (optionnel)

Les données existantes seront conservées :
  - sale_date sera remplie avec la date du jour pour les ventes déjà enregistrées.
  - sale_mode sera 'detail' pour toutes les lignes existantes.
  - pack_size sera 1 pour tous les produits existants.

RÉSUMÉ DES AMÉLIORATIONS
=========================

1. CADRES / DESIGN (base.html inchangé)
   → Les tableaux ont maintenant des en-têtes bleu dégradé bien contrastées.
   → Les cartes ont des coins arrondis, ombres douces.
   → Les pages ont un design plus propre.

2. IMAGE DE FOND SUR LA FACTURE (sale_invoice.html)
   → Allez dans Paramètres → "Image de fond facture"
   → L'image apparaît en filigrane (10% opacité) derrière les articles.
   → Fonctionne aussi à l'impression.

3. ZOOM IMAGE PRODUITS (product_list.html)
   → Survolez une image → zoom x2.2 en place.
   → Cliquez → modale agrandie plein écran.

4. VENTE PAR PAQUET (models.py + create_sale.html)
   → Ajoutez pack_size sur chaque produit (ex: 12 pour une boîte de 12).
   → Dans "Créer une vente", choisissez "Paquet" → le prix et le stock sont calculés automatiquement.
   → La facture affiche le mode (Détail / Paquet).

5. ENREGISTREMENT DIFFÉRÉ (create_sale.html + models.py)
   → Champ "Date de la vente" modifiable.
   → Vous pouvez saisir hier ou avant-hier si la vente était sur papier.
   → Le tableau de bord et les statistiques respectent cette date.

6. TRI DES LISTES (views.py + product_list.html)
   → Cliquez sur les en-têtes de colonnes : Nom, Prix, Stock, Catégorie, Expiration.
   → Cliquez à nouveau pour inverser l'ordre (ascendant ↔ descendant).
   → Fonctionne aussi sur l'historique des ventes et les dépenses.
"""

print("Lisez ce fichier pour les instructions de migration.")

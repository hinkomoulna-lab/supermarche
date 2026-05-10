from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # DASHBOARD
    path('', views.home, name='home'),
    path('parametres/', views.store_settings_view, name='store_settings'),
    path('acces-telephone/', views.mobile_access, name='mobile_access'),
    path('base-donnees/', views.database_tools, name='database_tools'),
    path('base-donnees/sauvegarde/', views.database_backup, name='database_backup'),
    path('base-donnees/export-json/', views.database_export_json, name='database_export_json'),
    path('base-donnees/importer-json/', views.database_import_json, name='database_import_json'),
    path('fonctionnalites/', views.feature_list, name='feature_list'),
    path('fonctionnalites/assistant-ia/', views.ai_feature_assistant, name='ai_feature_assistant'),
    path('fonctionnalites/nouveau/', views.feature_create, name='feature_create'),
    path('fonctionnalites/<int:pk>/modifier/', views.feature_update, name='feature_update'),
    path('fonctionnalites/<int:pk>/supprimer/', views.feature_delete, name='feature_delete'),
    path('guide-modifications/', views.modification_guide, name='modification_guide'),
    path('comptes/nouveau/', views.account_create, name='account_create'),

    # PRODUITS
    path('produits/', views.product_list, name='product_list'),
    path('produits/gestion/', views.product_manage, name='product_manage'),
    path('produits/gestion/nouveau/', views.product_create, name='product_create'),
    path('produits/gestion/<int:pk>/modifier/', views.product_update, name='product_update'),
    path('produits/gestion/<int:pk>/supprimer/', views.product_delete, name='product_delete'),

    # VENTES
    path('vente/', views.create_sale, name='create_sale'),
    path('ventes/', views.sale_history, name='sale_history'),
    path('ventes/suppression-groupee/', views.sale_bulk_delete, name='sale_bulk_delete'),
    path('ventes/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('ventes/<int:sale_id>/modifier/', views.sale_update, name='sale_update'),
    path('ventes/<int:sale_id>/supprimer/', views.sale_delete, name='sale_delete'),
    path('ventes/<int:sale_id>/facture/', views.sale_invoice, name='sale_invoice'),
    path('ventes/<int:sale_id>/facture/pdf/', views.sale_invoice_pdf, name='sale_invoice_pdf'),
    path('ventes/export/', views.export_sales_csv, name='export_sales_csv'),

    # PANIER
    path('panier/', views.cart_view, name='cart'),
    path('panier/ajouter/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('panier/supprimer/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('panier/valider/', views.cart_checkout, name='cart_checkout'),

    # DÉPENSES
    path('depenses/', views.expense_list, name='expense_list'),
    path('depenses/nouveau/', views.expense_create, name='expense_create'),
    path('depenses/<int:pk>/modifier/', views.expense_update, name='expense_update'),
    path('depenses/<int:pk>/supprimer/', views.expense_delete, name='expense_delete'),

    # DETTES
    path('dettes/', views.debt_list, name='debt_list'),
    path('dettes/nouveau/', views.debt_create, name='debt_create'),
    path('dettes/<int:pk>/modifier/', views.debt_update, name='debt_update'),
    path('dettes/<int:pk>/supprimer/', views.debt_delete, name='debt_delete'),
    path('dettes/<int:pk>/regler/', views.debt_mark_paid, name='debt_mark_paid'),

    # CRÉDITS TÉLÉPHONIQUES
    path('credits-telephoniques/', views.phone_credit_list, name='phone_credit_list'),
    path('credits-telephoniques/nouveau/', views.phone_credit_create, name='phone_credit_create'),
    path('credits-telephoniques/<int:pk>/modifier/', views.phone_credit_update, name='phone_credit_update'),
    path('credits-telephoniques/<int:pk>/supprimer/', views.phone_credit_delete, name='phone_credit_delete'),

    # ACHATS CRÉDITS
    path('achats-credits/', views.phone_credit_purchase_list, name='phone_credit_purchase_list'),
    path('achats-credits/nouveau/', views.phone_credit_purchase_create, name='phone_credit_purchase_create'),
    path('achats-credits/<int:pk>/modifier/', views.phone_credit_purchase_update, name='phone_credit_purchase_update'),
    path('achats-credits/<int:pk>/supprimer/', views.phone_credit_purchase_delete, name='phone_credit_purchase_delete'),

    # PERTES DE STOCK
    path('pertes/', views.stock_loss_list, name='stock_loss_list'),
    path('pertes/perimes/', views.stock_loss_expired, name='stock_loss_expired'),
    path('pertes/nouveau/', views.stock_loss_create, name='stock_loss_create'),
]

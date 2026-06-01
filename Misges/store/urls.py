from django.urls import path
from . import views
from . import api

app_name = 'store'

urlpatterns = [
    # DASHBOARD
    path('', views.home, name='home'),
    path('parametres/', views.store_settings_view, name='store_settings'),
    path('acces-telephone/', views.mobile_access, name='mobile_access'),
    path('appareils-connectes/', views.connected_devices, name='connected_devices'),
    path('appareils-connectes/<str:session_key>/deconnecter/', views.disconnect_device, name='disconnect_device'),
    path('base-donnees/', views.database_tools, name='database_tools'),
    path('base-donnees/sauvegarde/', views.database_backup, name='database_backup'),
    path('base-donnees/sauvegarde-auto/', views.database_auto_backup, name='database_auto_backup'),
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
    path('produits/top/', views.top_products, name='top_products'),
    path('inventaire/', views.inventory_list, name='inventory_list'),
    path('produits/gestion/', views.product_manage, name='product_manage'),
    path('produits/gestion/nouveau/', views.product_create, name='product_create'),
    path('produits/gestion/<int:pk>/modifier/', views.product_update, name='product_update'),
    path('produits/gestion/<int:pk>/supprimer/', views.product_delete, name='product_delete'),
    path('produits/gestion/<int:pk>/approvisionner/', views.product_supply, name='product_supply'),
    path('produits/gestion/<int:pk>/stock-rapide/', views.product_quick_stock, name='product_quick_stock'),
    path('produits/gestion/<int:pk>/dupliquer/', views.product_duplicate, name='product_duplicate'),
    path('produits/gestion/rupture/', views.out_of_stock, name='out_of_stock'),
    path('produits/gestion/prix-lot/', views.bulk_price_update, name='bulk_price_update'),
    path('produits/gestion/<int:pk>/prix/', views.price_history, name='price_history'),
    path('approvisionnements/', views.supply_history, name='supply_history'),
    path('reception/', views.reception_list, name='reception_list'),
    path('reception/commande/<int:pk>/', views.reception_receive_order, name='reception_receive_order'),
    path('produits/etiquettes/', views.price_labels, name='price_labels'),
    path('produits/etiquettes/pdf/', views.price_labels_pdf, name='price_labels_pdf'),
    path('produits/<int:pk>/code-barres/', views.product_barcode_image, name='product_barcode_image'),

    # VENTES
    path('vente/', views.create_sale, name='create_sale'),
    path('vente/rapide/', views.quick_sale, name='quick_sale'),
    path('vente/api/chat/', views.chat_assistant, name='chat_assistant'),
    path('caisse/', views.pos_view, name='pos_view'),
    path('ventes/', views.sale_history, name='sale_history'),
    path('ventes/suppression-groupee/', views.sale_bulk_delete, name='sale_bulk_delete'),
    path('ventes/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('ventes/<int:sale_id>/modifier/', views.sale_update, name='sale_update'),
    path('ventes/<int:sale_id>/supprimer/', views.sale_delete, name='sale_delete'),
    path('ventes/<int:sale_id>/facture/', views.sale_invoice, name='sale_invoice'),
    path('ventes/<int:sale_id>/facture/pdf/', views.sale_invoice_pdf, name='sale_invoice_pdf'),
    path('ventes/<int:sale_id>/ticket/', views.sale_receipt, name='sale_receipt'),
    path('ventes/export/', views.export_sales_csv, name='export_sales_csv'),
    path('ventes/export-excel/', views.export_sales_excel, name='export_sales_excel'),
    path('produits/export-excel/', views.export_products_excel, name='export_products_excel'),
    path('produits/import-bulk/', views.product_import_bulk, name='product_import_bulk'),
    path('produits/reassort-auto/', views.auto_reorder, name='auto_reorder'),
    path('produits/batch-action/', views.product_batch_action, name='product_batch_action'),
    path('ventes/rapport-pdf/', views.sales_report_pdf, name='sales_report_pdf'),
    path('produits/reassort-auto/', views.auto_reorder, name='auto_reorder'),

    # RAPPORTS
    path('rapports/journalier/', views.daily_report_view, name='daily_report'),
    path('rapports/marge-jour/', views.daily_margin_data, name='daily_margin_data'),

    # INVENTAIRE RAPIDE
    path('inventaire/rapide/', views.quick_inventory, name='quick_inventory'),

    # HISTORIQUE STOCK
    path('produits/mouvements-stock/', views.stock_movement_history, name='stock_movement_history'),

    # SAUVEGARDE PROGRAMMÉE
    path('base-donnees/sauvegarde-schedule/', views.scheduled_backup, name='scheduled_backup'),

    # NETTOYAGE
    path('base-donnees/nettoyage/', views.cleanup_old_data, name='cleanup_old_data'),

    # ALERTE FOURNISSEUR
    path('produits/<int:pk>/alerte-fournisseur/', views.alert_supplier_rupture, name='alert_supplier_rupture'),

    # RACCOURCIS
    path('raccourcis-clavier/', views.keyboard_shortcuts_help, name='keyboard_shortcuts'),

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
    path('clients/', views.customer_list, name='customer_list'),
    path('clients/<int:pk>/historique/', views.customer_history, name='customer_history'),
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

    # CAISSE
    path('caisse/journal/', views.cash_session_list, name='cash_session_list'),
    path('caisse/ouvrir/', views.cash_session_open, name='cash_session_open'),
    path('caisse/fermer/<int:pk>/', views.cash_session_close, name='cash_session_close'),
    path('caisse/restaurer/<int:pk>/', views.cash_session_restore, name='cash_session_restore'),
    path('caisse/mouvement/', views.cash_movement_create, name='cash_movement_create'),

    # RETOURS
    path('retours/', views.return_list, name='return_list'),
    path('retours/nouveau/', views.return_create, name='return_create'),
    path('retours/<int:pk>/approuver/', views.return_approve, name='return_approve'),
    path('retours/<int:pk>/rejeter/', views.return_reject, name='return_reject'),

    # BÉNÉFICES
    path('tableau-de-bord/', views.dashboard_view, name='dashboard'),
    path('benefices/', views.profit_view, name='profit_view'),
    path('rapports/paiements/', views.payment_method_report, name='payment_method_report'),

    # MANUEL
    path('manuel/', views.user_manual, name='user_manual'),
    path('manuel-utilisation.pdf/', views.user_manual_pdf, name='user_manual_pdf'),

    # RECETTES / PRODUITS COMPOSITES
    path('recettes/', views.recipe_list, name='recipe_list'),
    path('recettes/nouveau/', views.recipe_create, name='recipe_create'),
    path('recettes/<int:pk>/modifier/', views.recipe_edit, name='recipe_edit'),
    path('recettes/<int:pk>/supprimer/', views.recipe_delete, name='recipe_delete'),

    # RAPPORTS
    path('rapports/valorisation-stock/', views.stock_valuation_report, name='stock_valuation'),

    # EMPLOYÉS
    path('employes/', views.employee_list, name='employee_list'),
    path('employes/nouveau/', views.employee_create, name='employee_create'),
    path('employes/<int:pk>/modifier/', views.employee_edit, name='employee_edit'),
    path('employes/<int:pk>/supprimer/', views.employee_delete, name='employee_delete'),

    # POINTAGE
    path('pointage/', views.attendance_list, name='attendance_list'),
    path('pointage/arrivee/<int:pk>/', views.attendance_clock_in, name='attendance_clock_in'),
    path('pointage/depart/<int:pk>/', views.attendance_clock_out, name='attendance_clock_out'),

    # PAIE / RH
    path('paie/', views.payroll_report, name='payroll_report'),
    path('rh/', views.rh_dashboard, name='rh_dashboard'),

    # RAPPORTS
    path('rapports/marges/', views.margin_report, name='margin_report'),

    # API REST
    path('api/products/', api.api_product_list, name='api_product_list'),
    path('api/products/<int:pk>/', api.api_product_detail, name='api_product_detail'),
    path('api/categories/', api.api_categories, name='api_categories'),
    path('api/promotions/', api.api_active_promotions, name='api_active_promotions'),
    path('api/create-sale/', api.api_create_sale, name='api_create_sale'),
    path('api/login/', api.api_login, name='api_login'),
    path('api/me/', api.api_me, name='api_me'),
    path('api/cancel-sale/<int:sale_id>/', api.api_cancel_sale, name='api_cancel_sale'),
    path('api/reset-sales/', api.api_reset_sales, name='api_reset_sales'),
    path('api/sale-history/', api.api_sale_history, name='api_sale_history'),
]

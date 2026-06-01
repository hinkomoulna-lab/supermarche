"""
Migrate all data from Django SQLite DB to MAUI EF Core SQLite DB.

Usage: python scripts/migrate_data.py
Requires: Run the MAUI app at least once to create the new database.
"""
import sqlite3
import os
import sys

OLD_DB = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')

# Use absolute path to avoid encoding issues
NEW_DB = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Release\net9.0-windows10.0.19041.0\win-x64\publish\supermarché.db'
if not os.path.exists(NEW_DB):
    NEW_DB = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Debug\net9.0-windows10.0.19041.0\win10-x64\supermarché.db'

if not NEW_DB:
    print("ERROR: New database not found.")
    print("Run the MAUI app first to create it at one of these paths:")
    for p in NEW_DB_CANDIDATES:
        print(f"  {p}")
    sys.exit(1)

# Column mappings: old_table -> (new_table, {old_col: new_col})
MAPPINGS = {
    'store_category': ('categories', {
        'id': 'Id', 'name': 'Name', 'description': 'Description', 'created_at': 'CreatedAt'}),
    'store_supplier': ('suppliers', {
        'id': 'Id', 'name': 'Name', 'contact_person': 'ContactPerson',
        'phone': 'Phone', 'email': 'Email', 'address': 'Address', 'created_at': 'CreatedAt'}),
    'store_customer': ('customers', {
        'id': 'Id', 'name': 'Name', 'phone': 'Phone', 'email': 'Email',
        'address': 'Address', 'credit_limit': 'CreditLimit',
        'outstanding_balance': 'OutstandingBalance', 'created_at': 'CreatedAt'}),
    'store_product': ('products', {
        'id': 'Id', 'name': 'Name', 'barcode': 'Barcode', 'description': 'Description',
        'buy_price': 'BuyPrice', 'sell_price': 'SellPrice', 'wholesale_price': 'WholesalePrice',
        'margin_percent': 'MarginPercent', 'stock': 'Stock', 'min_stock': 'MinStock',
        'unit': 'Unit', 'carton_size': 'CartonSize', 'image': 'ImagePath',
        'is_active': 'IsActive', 'expiry_date': 'ExpiryDate',
        'category_id': 'CategoryId', 'supplier_id': 'SupplierId', 'created_at': 'CreatedAt'}),
    'store_sale': ('sales', {
        'id': 'Id', 'receipt_number': 'ReceiptNumber', 'total': 'Total',
        'discount': 'Discount', 'amount_paid': 'AmountPaid', 'change_given': 'ChangeGiven',
        'payment_status': 'PaymentStatus', 'payment_method': 'PaymentMethod',
        'payment_phone': 'PaymentPhone', 'currency': 'Currency',
        'tva_rate': 'TvaRate', 'tva_amount': 'TvaAmount', 'notes': 'Notes',
        'customer_id': 'CustomerId', 'cash_session_id': 'CashSessionId',
        'user_profile_id': 'UserProfileId', 'sold_at': 'SoldAt'}),
    'store_saleitem': ('sale_items', {
        'id': 'Id', 'sale_id': 'SaleId', 'product_id': 'ProductId',
        'quantity': 'Quantity', 'unit_price': 'UnitPrice',
        'total_price': 'TotalPrice', 'sale_mode': 'SaleMode'}),
    'store_expense': ('expenses', {
        'id': 'Id', 'title': 'Title', 'amount': 'Amount', 'category': 'Category',
        'is_investment': 'IsInvestment', 'notes': 'Notes',
        'incurred_at': 'IncurredAt', 'created_at': 'CreatedAt'}),
    'store_debt': ('debts', {
        'id': 'Id', 'debtor_name': 'DebtorName', 'phone': 'Phone',
        'amount': 'Amount', 'amount_paid': 'AmountPaid', 'paid': 'Paid',
        'due_date': 'DueDate', 'notes': 'Notes', 'customer_id': 'CustomerId',
        'created_at': 'CreatedAt'}),
    'store_cashsession': ('cash_sessions', {
        'id': 'Id', 'opening_balance': 'OpeningBalance',
        'closing_balance': 'ClosingBalance', 'opened_at': 'OpenedAt',
        'closed_at': 'ClosedAt', 'is_open': 'IsOpen'}),
    'store_cashmovement': ('cash_movements', {
        'id': 'Id', 'cash_session_id': 'CashSessionId', 'amount': 'Amount',
        'direction': 'Direction', 'reason': 'Reason', 'moved_at': 'MovedAt'}),
    'store_inventoryadjustment': ('inventory_adjustments', {
        'id': 'Id', 'product_id': 'ProductId', 'previous_stock': 'PreviousStock',
        'new_stock': 'NewStock', 'difference': 'Difference',
        'reason': 'Reason', 'adjusted_at': 'AdjustedAt'}),
    'store_userprofile': ('user_profiles', {
        'id': 'Id', 'username': 'Username', 'full_name': 'FullName',
        'role': 'Role', 'email': 'Email', 'is_active': 'IsActive',
        'created_at': 'CreatedAt'}),
    'store_phonecredit': ('phone_credits', {
        'id': 'Id', 'phone_number': 'PhoneNumber', 'amount': 'Amount',
        'operator': 'Operator', 'sold_at': 'SoldAt'}),
    'store_phonecreditpurchase': ('phone_credit_purchases', {
        'id': 'Id', 'amount': 'Amount', 'operator': 'Operator',
        'purchased_at': 'PurchasedAt'}),
    'store_storesettings': ('store_settings', {
        'id': 'Id', 'store_name': 'StoreName', 'welcome_message': 'WelcomeMessage',
        'scripture_mode': 'ScriptureMode', 'language': 'Language',
        'logo': 'Logo', 'background_image': 'BackgroundImage',
        'invoice_watermark': 'InvoiceWatermark', 'theme': 'Theme',
        'invoice_layout': 'InvoiceLayout', 'address': 'Address',
        'phone_number': 'PhoneNumber', 'signature': 'Signature',
        'currency': 'Currency', 'eur_rate': 'EurRate', 'usd_rate': 'UsdRate',
        'voice_alerts': 'VoiceAlerts', 'monthly_expense_limit': 'MonthlyExpenseLimit',
        'sms_api_key': 'SmsApiKey', 'sms_from': 'SmsFrom',
        'whatsapp_api_key': 'WhatsAppApiKey',
        'whatsapp_phone_number_id': 'WhatsAppPhoneNumberId',
        'default_bank_account_id': 'DefaultBankAccountId'}),
    'store_appfeature': ('app_features', {
        'id': 'Id', 'title': 'Title', 'description': 'Description',
        'code_notes': 'CodeNotes', 'status': 'Status', 'created_at': 'CreatedAt'}),
    'store_purchaseorder': ('purchase_orders', {
        'id': 'Id', 'order_number': 'OrderNumber', 'supplier_id': 'SupplierId',
        'total_amount': 'TotalAmount', 'status': 'Status', 'ordered_at': 'OrderedAt'}),
    'store_purchaseorderitem': ('purchase_order_items', {
        'id': 'Id', 'purchase_order_id': 'PurchaseOrderId',
        'product_id': 'ProductId', 'quantity': 'Quantity',
        'unit_price': 'UnitPrice', 'total_price': 'TotalPrice'}),
    'store_promotion': ('promotions', {
        'id': 'Id', 'name': 'Name', 'product_id': 'ProductId',
        'discount_percent': 'DiscountPercent', 'start_date': 'StartDate',
        'end_date': 'EndDate', 'is_active': 'IsActive'}),
    'store_customerorder': ('customer_orders', {
        'id': 'Id', 'order_number': 'OrderNumber', 'customer_id': 'CustomerId',
        'total_amount': 'TotalAmount', 'status': 'Status', 'ordered_at': 'OrderedAt'}),
    'store_customerorderitem': ('customer_order_items', {
        'id': 'Id', 'customer_order_id': 'CustomerOrderId',
        'product_id': 'ProductId', 'quantity': 'Quantity',
        'unit_price': 'UnitPrice', 'total_price': 'TotalPrice'}),
    'store_productreturn': ('product_returns', {
        'id': 'Id', 'sale_id': 'SaleId', 'reason': 'Reason',
        'total_refund': 'TotalRefund', 'returned_at': 'ReturnedAt'}),
    'store_productreturnitem': ('product_return_items', {
        'id': 'Id', 'product_return_id': 'ProductReturnId',
        'product_id': 'ProductId', 'quantity': 'Quantity',
        'refund_amount': 'RefundAmount'}),
    'store_stockloss': ('stock_losses', {
        'id': 'Id', 'product_id': 'ProductId', 'quantity': 'Quantity',
        'reason': 'Reason', 'total_value': 'TotalValue',
        'recorded_at': 'RecordedAt'}),
    'store_supplierreturn': ('supplier_returns', {
        'id': 'Id', 'supplier_id': 'SupplierId', 'reason': 'Reason',
        'total_refund': 'TotalRefund', 'returned_at': 'ReturnedAt'}),
    'store_supplierreturnitem': ('supplier_return_items', {
        'id': 'Id', 'supplier_return_id': 'SupplierReturnId',
        'product_id': 'ProductId', 'quantity': 'Quantity',
        'refund_amount': 'RefundAmount'}),
    'store_bankaccount': ('bank_accounts', {
        'id': 'Id', 'account_name': 'AccountName',
        'account_number': 'AccountNumber', 'bank_name': 'BankName',
        'balance': 'Balance'}),
    'store_banktransaction': ('bank_transactions', {
        'id': 'Id', 'bank_account_id': 'BankAccountId', 'amount': 'Amount',
        'type': 'Type', 'description': 'Description',
        'transacted_at': 'TransactedAt'}),
    'store_loyaltyprogram': ('loyalty_programs', {
        'id': 'Id', 'name': 'Name', 'points_per_amount': 'PointsPerAmount',
        'redeem_rate': 'RedeemRate', 'is_active': 'IsActive'}),
    'store_loyaltytransaction': ('loyalty_transactions', {
        'id': 'Id', 'customer_id': 'CustomerId', 'points': 'Points',
        'type': 'Type', 'transacted_at': 'TransactedAt'}),
    'store_solarcomponent': ('solar_components', {
        'id': 'Id', 'name': 'Name', 'type': 'Type',
        'unit_price': 'UnitPrice', 'stock': 'Stock'}),
    'store_solarproject': ('solar_projects', {
        'id': 'Id', 'project_name': 'ProjectName', 'client_name': 'ClientName',
        'client_phone': 'ClientPhone', 'total_cost': 'TotalCost',
        'selling_price': 'SellingPrice', 'actual_profit': 'ActualProfit',
        'status': 'Status', 'created_at': 'CreatedAt'}),
    'store_solarprojectitem': ('solar_project_items', {
        'id': 'Id', 'solar_project_id': 'SolarProjectId',
        'solar_component_id': 'SolarComponentId', 'description': 'Description',
        'quantity': 'Quantity', 'unit_price': 'UnitPrice',
        'total_price': 'TotalPrice'}),
    'store_giftcard': ('gift_cards', {
        'id': 'Id', 'code': 'Code', 'initial_balance': 'InitialBalance',
        'current_balance': 'CurrentBalance', 'created_at': 'CreatedAt',
        'expires_at': 'ExpiresAt', 'is_active': 'IsActive'}),
    'store_giftcardusage': ('gift_card_usages', {
        'id': 'Id', 'gift_card_id': 'GiftCardId', 'sale_id': 'SaleId',
        'amount_used': 'AmountUsed', 'used_at': 'UsedAt'}),
    'store_activitylog': ('activity_logs', {
        'id': 'Id', 'action': 'Action', 'description': 'Description',
        'user': 'User', 'timestamp': 'Timestamp'}),
    'store_coiffureclient': ('coiffure_clients', {
        'id': 'Id', 'name': 'Name', 'phone': 'Phone',
        'notes': 'Notes', 'created_at': 'CreatedAt'}),
}


def migrate():
    old = sqlite3.connect(OLD_DB)
    old.row_factory = sqlite3.Row
    new = sqlite3.connect(NEW_DB)
    new.execute("PRAGMA foreign_keys = OFF")

    # Get new table columns
    new_tables = {}
    cursor = new.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        name = row[0]
        if name.startswith('__'):
            continue
        cols = [c[1] for c in new.execute(f'PRAGMA table_info("{name}")').fetchall()]
        new_tables[name] = cols

    total = 0
    for old_table, (new_table, col_map) in MAPPINGS.items():
        try:
            rows = old.execute(f'SELECT * FROM "{old_table}"').fetchall()
        except sqlite3.OperationalError:
            continue

        if not rows:
            print(f"  {old_table} -> {new_table}: 0 rows")
            continue

        if new_table not in new_tables:
            print(f"  WARNING: {new_table} not in new DB, skipping")
            continue

        new_cols = new_tables[new_table]

        count = 0
        for row in rows:
            vals = []
            for nc in new_cols:
                # Find the old column that maps to this new column
                old_col = None
                for oc, nwc in col_map.items():
                    if nwc == nc:
                        old_col = oc
                        break
                if old_col and old_col in row.keys():
                    vals.append(row[old_col])
                else:
                    vals.append(None)

            placeholders = ','.join(['?' for _ in new_cols])
            cols_str = ','.join(f'"{c}"' for c in new_cols)

            try:
                new.execute(f'INSERT OR IGNORE INTO "{new_table}" ({cols_str}) VALUES ({placeholders})', vals)
                count += 1
            except sqlite3.IntegrityError as e:
                if 'UNIQUE' not in str(e):
                    print(f"    Error: {e}")

        new.commit()
        print(f"  {old_table} -> {new_table}: {count} rows")
        total += count

    new.execute("PRAGMA foreign_keys = ON")
    new.close()
    old.close()
    print(f"\nMigration complete! {total} total rows migrated.")


if __name__ == '__main__':
    migrate()

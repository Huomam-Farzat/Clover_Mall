from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
import pandas as pd
from .models import Transaction

def mine_frequent_itemsets():
    # Retrieve transaction data
    transactions = Transaction.objects.all()

    # Check if there are any transactions
    if not transactions:
        return []

    # Prepare transaction data for FP-Growth
    transaction_data = []
    for transaction in transactions:
        product_names = [product.name for product in transaction.products.all()]
        transaction_data.append(product_names)

    # Check if there is enough data for analysis
    if not transaction_data:
        return []

    # Apply FP-Growth algorithm
    te = TransactionEncoder()
    te_ary = te.fit(transaction_data).transform(transaction_data)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    
    # Mine frequent itemsets
    frequent_itemsets = fpgrowth(df, min_support=0.25, use_colnames=True)

    # Convert DataFrame to list of dictionaries
    frequent_itemsets_list = frequent_itemsets.to_dict(orient='records')

    # Mine association rules from frequent itemsets
    rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=0.8)
    rules_list = rules.to_dict(orient='records')

    return rules_list

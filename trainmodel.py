import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

print("Connecting to database...")
# Replace YOUR_ACTUAL_PASSWORD with your MySQL root password
engine = create_engine("mysql+pymysql://root:Yonkoluffy$3B@localhost:3306/paysim")

print("Fetching transaction data...")
# Pulling all existing rows from paysim_sample/paysim_raw(in SQL)
query = """
SELECT step, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, isFraud 
FROM paysim_raw 
LIMIT 50000
"""
df = pd.read_sql(query, con=engine)

# Features & Target
X = df[['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']]
y = df['isFraud']

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training Random Forest model...")
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("\n--- Model Evaluation ---")
print(classification_report(y_test, y_pred))

# Save
joblib.dump(model, 'fraud_model.pkl')
print("Model saved successfully as 'fraud_model.pkl'!")
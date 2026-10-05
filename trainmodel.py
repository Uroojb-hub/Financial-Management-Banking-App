import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from lightgbm import LGBMClassifier
import shap

print("⚡ Connecting to MySQL Database...")
engine = create_engine("mysql+pymysql://root:Yonkoluffy$3B@localhost:3306/paysim")

query = """
SELECT step, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, isFraud 
FROM paysim_raw 
LIMIT 50000
"""
df = pd.read_sql(query, con=engine)

# 1. Feature Engineering
df['errorBalanceOrig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']
df['errorBalanceDest'] = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']

features = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
            'oldbalanceDest', 'newbalanceDest', 'errorBalanceOrig', 'errorBalanceDest']
X = df[features]
y = df['isFraud']

# 2. Train / Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. Train LightGBM Classifier
print("🧠 Training LightGBM Model with Class Weights...")
model = LGBMClassifier(
    n_estimators=100,
    learning_rate=0.05,
    scale_pos_weight=10,  # Focus on rare fraud cases
    random_state=42
)
model.fit(X_train, y_train)

# 4. Evaluation
preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1]
print("\n--- LightGBM Model Performance ---")
print(classification_report(y_test, preds))
print(f"ROC-AUC Score: {roc_auc_score(y_test, probs):.4f}")

# 5. Build SHAP Explainer
print("🔍 Building SHAP Explainer...")
explainer = shap.TreeExplainer(model)

# 6. Save Artifacts
joblib.dump(model, 'fraud_model.pkl')
joblib.dump(explainer, 'shap_explainer.pkl')
print("✅ Saved 'fraud_model.pkl' and 'shap_explainer.pkl' successfully!")
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np

app = FastAPI(title="PaySim Enterprise ML Engine", version="2.0")

# Load ML Artifacts
try:
    model = joblib.load('fraud_model.pkl')
    explainer = joblib.load('shap_explainer.pkl')
    print("✅ Model & SHAP Explainer loaded successfully!")
except Exception as e:
    model, explainer = None, None
    print(f"⚠️ Warning: Could not load ML artifacts - {e}")

class TransactionRequest(BaseModel):
    step: int
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict_fraud")
def predict_fraud(transaction: TransactionRequest):
    if model is None or explainer is None:
        raise HTTPException(status_code=500, detail="ML Services uninitialized.")

    # Engineering features matching training
    err_orig = transaction.newbalanceOrig + transaction.amount - transaction.oldbalanceOrg
    err_dest = transaction.oldbalanceDest + transaction.amount - transaction.newbalanceDest

    features = ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 
                'oldbalanceDest', 'newbalanceDest', 'errorBalanceOrig', 'errorBalanceDest']
    
    input_data = pd.DataFrame([[
        transaction.step, transaction.amount, transaction.oldbalanceOrg,
        transaction.newbalanceOrig, transaction.oldbalanceDest,
        transaction.newbalanceDest, err_orig, err_dest
    ]], columns=features)

    # Predictions
    prediction = int(model.predict(input_data)[0])
    probability = float(model.predict_proba(input_data)[0][1])

    # SHAP Feature Importance
    shap_values = explainer.shap_values(input_data)
    # Handle list or array return formats for TreeExplainer
    vals = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]
    top_feature_idx = np.argmax(np.abs(vals))
    top_feature_name = features[top_feature_idx]

    return {
        "prediction": prediction,
        "fraud_probability": round(probability, 4),
        "status": "success",
        "risk_level": "HIGH" if probability > 0.5 else "LOW",
        "top_risk_driver": top_feature_name,
        "details": transaction.model_dump()
    }
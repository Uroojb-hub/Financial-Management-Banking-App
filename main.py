from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import joblib
import pandas as pd

app = FastAPI(title="PaySim Mock Banking & Fraud Detection API", version="1.0")

# Load the trained ML Model artifact
try:
    model = joblib.load('fraud_model.pkl')
    print("Fraud Detection Model loaded successfully!")
except Exception as e:
    model = None
    print(f"Warning: Could not load fraud_model.pkl - {e}")

# Pydantic Schema for Input Validation
class TransactionRequest(BaseModel):
    step: int
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

@app.get("/")
def root():
    return {"message": "Welcome to PaySim Core Banking API", "status": "Online"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

# REST Endpoint: Score Fraud Risk for a Transaction
@app.post("/predict_fraud")
def predict_fraud(transaction: TransactionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="ML Model not available on server.")
    
    input_data = pd.DataFrame([[
        transaction.step,
        transaction.amount,
        transaction.oldbalanceOrg,
        transaction.newbalanceOrig,
        transaction.oldbalanceDest,
        transaction.newbalanceDest
    ]], columns=['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest'])

    prediction = int(model.predict(input_data)[0])
    probability = float(model.predict_proba(input_data)[0][1])

    return {
        "is_fraud": prediction == 1,
        "fraud_probability": round(probability, 4),
        "risk_level": "HIGH" if probability > 0.5 else "LOW",
        "details": transaction.dict()
    }
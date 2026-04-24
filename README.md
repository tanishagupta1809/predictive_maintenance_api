# Predictive Maintenance System - Industrial Machine AI

Complete production-ready predictive maintenance system with ML backend and Java UI.

---

## ⚡ QUICK START (5 minutes)

### Open 4 Terminal Windows and Run:

**Terminal 1: Setup (First time only)**
```bash
cd /Users/tanishagupta/predictive_maintenance_api\ copy
pip install -r requirements.txt
python ml_model_train_improved.py
```
⏱️ Wait for: "Training pipeline completed successfully!" (~2-3 minutes)

**Terminal 2: Start API**
```bash
cd /Users/tanishagupta/predictive_maintenance_api\ copy/ml_api
cp ../ml_utils.py . && python app_improved.py
```
API running on http://localhost:5001

**Terminal 3: Build & Launch Web UI (Spring Boot) - First time only**
```bash
cd /Users/tanishagupta/predictive_maintenance_api\ copy/springboot-app
mvn clean package -DskipTests -q
java -jar target/demo-0.0.1-SNAPSHOT.jar
```
Web UI opens on http://localhost:8080

**Terminal 4: Verify**
```bash
curl http://localhost:5001/health
```
Should show: `"status": "healthy"`

---

## System Overview

```
┌─────────────────────────────────────────┐
│     JAVA UI (Desktop/Web)               │
│   Connected to ML API via HTTP          │
└────────────────┬────────────────────────┘
                 │
          http://5001/predict
                 │
┌────────────────▼────────────────────────┐
│      ML API (Flask)                     │
│   - Single & Batch Predictions          │
│   - Health Checks                       │
│   - Model Info                          │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   TRAINED ML MODELS                     │
│   - Failure Prediction (98.1% acc)      │
│   - Fault Classification (87.1% acc)    │
└─────────────────────────────────────────┘
```

---

## Project Files

### Essential Files
- **`ml_utils.py`** - Shared utilities
- **`ml_model_train_improved.py`** - Training script
- **`ml_api/app_improved.py`** - API server 
- **`requirements.txt`** - Python dependencies
- **`models/`** - Trained models (8 files, 7.4 MB)

### Java UI Options
- **`springboot-app/`** - Web UI (Spring Boot) ⭐ RECOMMENDED (works out of box)
- **`javafx_app/`** - Desktop GUI (requires JavaFX SDK download)
- **`servletApp/`** - Servlet-based UI

### Documentation
- **`START.md`** - Detailed overview
- **`RUN.md`** - Step-by-step guide
- **`COMMANDS.md`** - All commands
- **`QUICK.txt`** - Ultra-quick reference

---

## Features

**ML Models**
- Failure prediction: 98.1% accuracy
- Fault classification: 87.1% accuracy
- Real-time predictions: <50ms per request

 **API**
- Prediction endpoints (single & batch)
- Health checks
- Input validation
- Comprehensive logging

**Java UI**
- Desktop application (JavaFX)
- Web interface (Spring Boot)
- Servlet-based option
- Real-time predictions

---

## API Endpoints

### Single Prediction
```bash
POST http://localhost:5001/predict
Content-Type: application/json

{
  "air_temp": 298.5,
  "process_temp": 310.5,
  "speed": 1500,
  "torque": 42.8,
  "tool_wear": 120,
  "type": "M"
}
```

### Batch Prediction
```bash
POST http://localhost:5001/predict/batch
```

### Health Check
```bash
GET http://localhost:5001/health
```

### Model Info
```bash
GET http://localhost:5001/info
```

---

## Model Performance

| Metric | Value |
|--------|-------|
| Failure Detection Accuracy | 98.10% |
| Precision | 78.85% |
| Recall | 60.29% |
| F1-Score | 68.33% |
| ROC-AUC | 95.89% |

### Top Features
1. Rotational speed (31.6%)
2. Torque (29.1%)
3. Tool wear (20.2%)

---

## Valid Input Ranges

- **Air Temperature:** 295-305 K
- **Process Temperature:** 305-320 K
- **Rotational Speed:** 1168-9009 rpm
- **Torque:** 3.8-76.6 Nm
- **Tool Wear:** 0-254 min
- **Machine Type:** H/M/L

---

## Restart Procedure

### After Initial Setup
```bash
# Terminal 1: Start API
cd /Users/tanishagupta/predictive_maintenance_api\ copy/ml_api
cp ../ml_utils.py . && python app_improved.py

# Terminal 2: Start Web UI
cd /Users/tanishagupta/predictive_maintenance_api\ copy/springboot-app
java -jar target/demo-0.0.1-SNAPSHOT.jar
```

### Retrain Models (If Needed)
```bash
cd /Users/tanishagupta/predictive_maintenance_api\ copy
rm -rf models/*
python ml_model_train_improved.py
```

### Rebuild Web UI (If Code Changes)
```bash
cd /Users/tanishagupta/predictive_maintenance_api\ copy/springboot-app
mvn clean package -DskipTests
```

---

## Troubleshooting

### API won't start
```bash
# Check port 5001 is free
lsof -i :5001

# Kill if needed
kill -9 <PID>

# Verify dependencies
pip install -r requirements.txt
```

### Models not found
```bash
# Check models directory
ls -lh models/

# Retrain if empty
python ml_model_train_improved.py
```

### Web UI can't connect to API
```bash
# Verify API is running
curl http://localhost:5001/health

# Verify Web UI is running
curl http://localhost:8080/
```

### Spring Boot won't start
```bash
# Check if port 8080 is already in use
lsof -i :8080

# Kill if needed
kill -9 <PID>

# Rebuild and run
cd springboot-app
mvn clean package -DskipTests
java -jar target/demo-0.0.1-SNAPSHOT.jar
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| `START.md` | Full overview & architecture |
| `RUN.md` | Complete setup guide |
| `COMMANDS.md` | All available commands |
| `QUICK.txt` | Ultra-quick reference |
| `README.md` | This file |

---

## Technology Stack

- **Backend:** Python, Flask, scikit-learn
- **ML:** Random Forest, GridSearchCV
- **UI:** JavaFX (Desktop), Spring Boot (Web)
- **API:** RESTful JSON

---

## Performance Specs

- **Training Time:** 2-3 minutes (first time)
- **Prediction Latency:** <50ms (single)
- **Batch Processing:** 1000 predictions in <1 second
- **Memory Usage:** ~200 MB

---

## Model Details

### Failure Prediction
- Algorithm: Random Forest (200 trees)
- Best parameters: max_depth=15, balanced class_weight
- Cross-validation: 5-fold

### Fault Classification
- Algorithm: Random Forest (200 trees)
- Classes: HDF, OSF, PWF, RNF, TWF
- Handles: Multi-class classification

---

## Deployment Options

### Development (Current)
```bash
python app_improved.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app_improved:app
```

### Docker
```bash
docker build -t predictive-maintenance .
docker run -p 5001:5001 predictive-maintenance
```

---

## Support

- Check documentation files
- Review API logs in terminal
- Verify models are trained: `ls models/`
- Test API health: `curl http://localhost:5001/health`

---

## Status

- **Version:** 1.0
- **Status:** Production Ready
- **Last Updated:** April 14, 2026
- **Tested:** Yes
- **Deployed:** Yes

---

## Next Steps

1. Follow QUICK START above
2. Train models (Terminal 1)
3. Start API (Terminal 2)
4. Launch UI (Terminal 3)
5. Make predictions!

---

**Ready to use!** 

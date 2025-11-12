"""
FastAPI Multi-Bureau Credit Report Service
Generate credit reports for Equifax, TransUnion, and Experian

Installation:
pip install fastapi uvicorn

Run:
uvicorn main:app --reload

Endpoints:
- POST /api/reports/generate - Generate report(s) for selected bureau(s)
- GET /api/reports/{report_id} - Get a specific report
- GET /api/reports - List all reports
- GET /api/reports/bureau/{bureau_name} - List reports by bureau
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import random
import uuid

app = FastAPI(
    title="Multi-Bureau Credit Report API",
    description="Generate credit reports for Equifax, TransUnion, and Experian",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
credit_reports_db: Dict[str, Dict[Any, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Generate 50 sample reports on startup"""
    print("🚀 Generating 50 sample reports on startup...")
    
    # Generate reports with different profiles
    profiles = ["excellent", "good", "fair", "poor"]
    bureaus = [Bureau.EQUIFAX, Bureau.TRANSUNION, Bureau.EXPERIAN]
    
    for i in range(50):
        # Rotate through different profiles and bureaus
        profile = profiles[i % len(profiles)]
        bureau = bureaus[i % len(bureaus)]
        
        request = ReportGenerateRequest(
            bureau=bureau,
            credit_profile=CreditProfile(profile),
            num_accounts=random.randint(3, 7)
        )
        
        try:
            generate_credit_reports(request)
        except Exception as e:
            print(f"Error generating report {i+1}: {e}")
    
    print(f"✅ Successfully generated {len(credit_reports_db)} sample reports")
    
    # Print statistics
    bureau_counts = {"equifax": 0, "transunion": 0, "experian": 0}
    for report in credit_reports_db.values():
        bureau = report.get("bureau", "").lower()
        if bureau in bureau_counts:
            bureau_counts[bureau] += 1
    
    print(f"📊 Reports by bureau: {bureau_counts}")

# Enums
class Bureau(str, Enum):
    EQUIFAX = "equifax"
    TRANSUNION = "transunion"
    EXPERIAN = "experian"
    ALL = "all"

class CreditProfile(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    RANDOM = "random"

# Sample data
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", 
               "Linda", "William", "Barbara", "David", "Elizabeth", "Richard", "Susan"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
              "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Thomas", "Taylor"]
CITIES = [
    ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"),
    ("Chicago", "IL", "60601"), ("Houston", "TX", "77001"),
    ("Phoenix", "AZ", "85001"), ("Philadelphia", "PA", "19101"),
]
STREET_NAMES = ["Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington"]
STREET_TYPES = ["St", "Ave", "Blvd", "Dr", "Ln", "Rd"]
EMPLOYERS = ["Tech Solutions Inc", "Global Consulting Group", "Retail America Corp"]
JOB_TITLES = ["Manager", "Analyst", "Engineer", "Developer", "Consultant"]
BANKS = ["Wells Fargo", "Bank of America", "Chase", "Citibank", "US Bank"]
CREDIT_CARDS = ["American Express", "Discover", "Capital One", "Barclays"]
AUTO_LENDERS = ["Toyota Financial", "GM Financial", "Ford Credit"]

# Helper functions
def generate_ssn():
    return random.randint(100000000, 999999999)

def generate_dob():
    year = random.randint(1950, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{month:02d}{day:02d}{year}"

def generate_date(days_ago_max=3650):
    days_ago = random.randint(30, days_ago_max)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime("%m%d%Y")

def generate_iso_date(days_ago_max=3650):
    days_ago = random.randint(30, days_ago_max)
    date = datetime.now() - timedelta(days=days_ago)
    return date.isoformat()

def generate_address():
    house_num = random.randint(100, 9999)
    street = random.choice(STREET_NAMES)
    street_type = random.choice(STREET_TYPES)
    city, state, zip_code = random.choice(CITIES)
    return {
        "houseNumber": house_num,
        "streetName": street,
        "streetType": street_type,
        "cityName": city,
        "stateAbbreviation": state,
        "zipCode": int(zip_code),
        "addressLine1": f"{house_num} {street} {street_type}"
    }

def get_credit_profile(profile_type):
    profiles = {
        "excellent": {"score": random.randint(750, 850), "delinquencies": 0},
        "good": {"score": random.randint(670, 749), "delinquencies": random.randint(0, 1)},
        "fair": {"score": random.randint(580, 669), "delinquencies": random.randint(1, 3)},
        "poor": {"score": random.randint(300, 579), "delinquencies": random.randint(3, 6)}
    }
    if profile_type == "random":
        profile_type = random.choice(list(profiles.keys()))
    return profile_type, profiles.get(profile_type, profiles["good"])

def generate_payment_history(profile_range, format="equifax"):
    months = 24
    if profile_range == "excellent":
        codes = [1] * months
    elif profile_range == "good":
        codes = [1] * (months - 2) + [2] * 2
    elif profile_range == "fair":
        codes = [1] * (months - 5) + [2, 2, 3, 2, 1]
    else:
        codes = [1] * (months - 8) + [2, 3, 4, 3, 2, 3, 4, 2]
    
    random.shuffle(codes)
    
    if format == "transunion":
        # TransUnion uses different codes
        return [{"code": f"R{code}" if code <= 4 else "R9", 
                "description": f"Payment status {code}"} for code in codes]
    elif format == "experian":
        # Experian uses 0-9 scale
        return [{"code": str(code) if code <= 9 else "9", 
                "description": f"Payment status {code}"} for code in codes]
    else:  # equifax
        descriptions = {
            1: "Pays account as agreed",
            2: "Not more than two payments past due",
            3: "Not more than three payments past due",
            4: "Not more than four payments past due"
        }
        return [{"code": code, "description": descriptions.get(code, "Status unknown")} 
                for code in codes]

# EQUIFAX Report Generator
def generate_equifax_report(first_name, last_name, middle_initial, ssn, dob, 
                           profile_range, profile_data, current_addr, former_addr, num_accounts):
    trades = []
    for _ in range(num_accounts):
        account_type = random.choice(["credit_card", "auto_loan", "mortgage"])
        trade = {
            "customerNumber": f"999{random.choice(['BB', 'FA', 'MT'])}{random.randint(10000, 99999)}",
            "accountNumber": random.randint(100000, 999999999),
            "dateReported": generate_date(365),
            "dateOpened": generate_date(),
            "rate": {"code": 1 if profile_range in ["excellent", "good"] else random.randint(1, 3)},
            "paymentHistory1to24": generate_payment_history(profile_range, "equifax"),
            "lastActivityDate": generate_date(180)
        }
        
        if account_type == "credit_card":
            trade.update({
                "customerName": random.choice(CREDIT_CARDS),
                "highCredit": random.randint(1000, 25000),
                "accountTypeCode": {"code": 18, "description": "Credit Card"}
            })
        elif account_type == "auto_loan":
            trade.update({
                "customerName": random.choice(AUTO_LENDERS),
                "highCredit": random.randint(10000, 50000),
                "accountTypeCode": {"code": 0, "description": "Auto"}
            })
        else:
            trade.update({
                "customerName": random.choice(BANKS),
                "highCredit": random.randint(100000, 500000),
                "accountTypeCode": {"code": 1, "description": "Mortgage"}
            })
        trades.append(trade)
    
    return {
        "bureau": "Equifax",
        "consumers": {
            "equifaxUSConsumerCreditReport": [{
                "subjectName": {
                    "firstName": first_name,
                    "lastName": last_name,
                    "middleName": middle_initial
                },
                "subjectSocialNum": ssn,
                "birthDate": dob,
                "addresses": [current_addr, former_addr],
                "trades": trades,
                "models": [{
                    "type": "FICO",
                    "modelNumber": "08",
                    "score": profile_data["score"]
                }]
            }]
        }
    }

# TRANSUNION Report Generator  
def generate_transunion_report(first_name, last_name, middle_initial, ssn, dob,
                               profile_range, profile_data, current_addr, former_addr, num_accounts):
    tradelines = []
    for _ in range(num_accounts):
        account_type = random.choice(["credit_card", "auto_loan", "mortgage"])
        tradeline = {
            "accountNumber": random.randint(100000, 999999999),
            "accountType": account_type.replace("_", " ").title(),
            "dateOpened": generate_iso_date(),
            "dateReported": generate_iso_date(365),
            "paymentHistory": generate_payment_history(profile_range, "transunion"),
            "accountRating": "R1" if profile_range in ["excellent", "good"] else "R2"
        }
        
        if account_type == "credit_card":
            tradeline.update({
                "creditorName": random.choice(CREDIT_CARDS),
                "creditLimit": random.randint(1000, 25000),
                "currentBalance": random.randint(0, 10000)
            })
        elif account_type == "auto_loan":
            tradeline.update({
                "creditorName": random.choice(AUTO_LENDERS),
                "originalAmount": random.randint(10000, 50000),
                "monthlyPayment": random.randint(200, 600)
            })
        else:
            tradeline.update({
                "creditorName": random.choice(BANKS),
                "originalAmount": random.randint(100000, 500000),
                "monthlyPayment": random.randint(800, 3500)
            })
        tradelines.append(tradeline)
    
    return {
        "bureau": "TransUnion",
        "CREDIT_RESPONSE": {
            "CreditRepositorySourceType": "TransUnion",
            "BORROWER": {
                "firstName": first_name,
                "lastName": last_name,
                "middleName": middle_initial,
                "ssn": ssn,
                "birthDate": dob,
                "addresses": [
                    {
                        "type": "Current",
                        "street": current_addr["addressLine1"],
                        "city": current_addr["cityName"],
                        "state": current_addr["stateAbbreviation"],
                        "zip": current_addr["zipCode"]
                    },
                    {
                        "type": "Prior",
                        "street": former_addr["addressLine1"],
                        "city": former_addr["cityName"],
                        "state": former_addr["stateAbbreviation"],
                        "zip": former_addr["zipCode"]
                    }
                ]
            },
            "CREDIT_FILE": {
                "tradelines": tradelines,
                "creditScore": {
                    "model": "VantageScore 3.0",
                    "score": profile_data["score"],
                    "scoreFactors": [
                        {"code": "01", "description": "Credit utilization"}
                    ]
                }
            }
        }
    }

# EXPERIAN Report Generator
def generate_experian_report(first_name, last_name, middle_initial, ssn, dob,
                            profile_range, profile_data, current_addr, former_addr, num_accounts):
    accounts = []
    for _ in range(num_accounts):
        account_type = random.choice(["credit_card", "auto_loan", "mortgage"])
        account = {
            "accountNumber": f"****{random.randint(1000, 9999)}",
            "accountType": account_type.replace("_", " ").title(),
            "dateOpened": generate_iso_date(),
            "dateReported": generate_iso_date(365),
            "paymentPattern": generate_payment_history(profile_range, "experian"),
            "accountStatus": "Open" if random.random() > 0.3 else "Closed"
        }
        
        if account_type == "credit_card":
            account.update({
                "creditorName": random.choice(CREDIT_CARDS),
                "creditLimit": random.randint(1000, 25000),
                "balance": random.randint(0, 10000),
                "pastDueAmount": 0 if profile_range in ["excellent", "good"] else random.randint(0, 500)
            })
        elif account_type == "auto_loan":
            account.update({
                "creditorName": random.choice(AUTO_LENDERS),
                "originalLoanAmount": random.randint(10000, 50000),
                "monthlyPayment": random.randint(200, 600),
                "remainingBalance": random.randint(5000, 40000)
            })
        else:
            account.update({
                "creditorName": random.choice(BANKS),
                "originalLoanAmount": random.randint(100000, 500000),
                "monthlyPayment": random.randint(800, 3500),
                "remainingBalance": random.randint(50000, 450000)
            })
        accounts.append(account)
    
    return {
        "bureau": "Experian",
        "creditProfile": {
            "consumerIdentity": {
                "name": {
                    "firstName": first_name,
                    "middleName": middle_initial,
                    "lastName": last_name
                },
                "ssn": ssn,
                "dateOfBirth": dob,
                "addresses": [
                    {
                        "addressType": "Current",
                        "streetAddress": current_addr["addressLine1"],
                        "city": current_addr["cityName"],
                        "state": current_addr["stateAbbreviation"],
                        "zipCode": current_addr["zipCode"]
                    },
                    {
                        "addressType": "Previous",
                        "streetAddress": former_addr["addressLine1"],
                        "city": former_addr["cityName"],
                        "state": former_addr["stateAbbreviation"],
                        "zipCode": former_addr["zipCode"]
                    }
                ]
            },
            "creditAccounts": accounts,
            "creditScore": {
                "scoreName": "Experian/Fair Isaac Risk Model V2",
                "scoreValue": profile_data["score"],
                "scoreFactors": [
                    {
                        "factorCode": "38",
                        "factorText": "Proportion of balance to limit is too high on revolving accounts"
                    }
                ]
            },
            "inquiries": [
                {
                    "inquiryDate": generate_iso_date(180),
                    "subscriberName": random.choice(BANKS),
                    "inquiryType": "Hard"
                }
                for _ in range(random.randint(0, 3))
            ]
        }
    }

# Models
class ReportGenerateRequest(BaseModel):
    bureau: Bureau = Bureau.ALL
    credit_profile: CreditProfile = CreditProfile.RANDOM
    num_accounts: Optional[int] = None
    include_employment: bool = True

class ReportGenerateResponse(BaseModel):
    report_ids: Dict[str, str]
    message: str
    credit_score: int
    consumer_name: str
    bureaus_generated: List[str]

# Main generation function
def generate_credit_reports(request: ReportGenerateRequest):
    first_name = random.choice(FIRST_NAMES)
    middle_initial = chr(random.randint(65, 90))
    last_name = random.choice(LAST_NAMES)
    ssn = generate_ssn()
    dob = generate_dob()
    
    profile_range, profile_data = get_credit_profile(request.credit_profile.value)
    current_addr = generate_address()
    former_addr = generate_address()
    num_accounts = request.num_accounts or random.randint(2, 8)
    
    reports = {}
    bureaus_to_generate = []
    
    if request.bureau == Bureau.ALL:
        bureaus_to_generate = [Bureau.EQUIFAX, Bureau.TRANSUNION, Bureau.EXPERIAN]
    else:
        bureaus_to_generate = [request.bureau]
    
    for bureau in bureaus_to_generate:
        report_id = str(uuid.uuid4())
        
        if bureau == Bureau.EQUIFAX:
            report = generate_equifax_report(
                first_name, last_name, middle_initial, ssn, dob,
                profile_range, profile_data, current_addr, former_addr, num_accounts
            )
        elif bureau == Bureau.TRANSUNION:
            report = generate_transunion_report(
                first_name, last_name, middle_initial, ssn, dob,
                profile_range, profile_data, current_addr, former_addr, num_accounts
            )
        else:  # EXPERIAN
            report = generate_experian_report(
                first_name, last_name, middle_initial, ssn, dob,
                profile_range, profile_data, current_addr, former_addr, num_accounts
            )
        
        report.update({
            "reportId": report_id,
            "generatedDate": datetime.now().isoformat(),
            "creditProfile": profile_range
        })
        
        credit_reports_db[report_id] = report
        reports[bureau.value] = report_id
    
    return reports, f"{first_name} {last_name}", profile_data["score"], [b.value for b in bureaus_to_generate]

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Multi-Bureau Credit Report API",
        "version": "2.0.0",
        "bureaus": ["Equifax", "TransUnion", "Experian"],
        "total_reports": len(credit_reports_db)
    }

@app.post("/api/reports/generate", response_model=ReportGenerateResponse)
async def create_credit_report(request: ReportGenerateRequest = ReportGenerateRequest()):
    """Generate credit report(s) for selected bureau(s)"""
    try:
        report_ids, consumer_name, credit_score, bureaus = generate_credit_reports(request)
        
        return ReportGenerateResponse(
            report_ids=report_ids,
            message=f"Generated {len(report_ids)} report(s)",
            credit_score=credit_score,
            consumer_name=consumer_name,
            bureaus_generated=bureaus
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/reports/generate-unlimited")
async def generate_unlimited_reports(
    count: int = Query(..., ge=1),
    bureau: Bureau = Bureau.ALL,
    credit_profile: CreditProfile = CreditProfile.RANDOM
):
    """Generate unlimited reports"""
    total_generated = 0
    
    for _ in range(count):
        request = ReportGenerateRequest(bureau=bureau, credit_profile=credit_profile)
        generate_credit_reports(request)
        total_generated += 1
    
    return {
        "message": f"Generated {total_generated} report(s)",
        "total_in_system": len(credit_reports_db)
    }

@app.get("/api/reports/random")
async def get_random_report(bureau: Optional[str] = None):
    """
    Get a random credit report
    
    - **bureau**: Optional - Filter by bureau (equifax, transunion, experian)
    """
    if not credit_reports_db:
        raise HTTPException(status_code=404, detail="No reports available. Generate some first!")
    
    # Filter by bureau if specified
    if bureau:
        filtered_reports = {
            rid: report for rid, report in credit_reports_db.items()
            if report.get("bureau", "").lower() == bureau.lower()
        }
        
        if not filtered_reports:
            raise HTTPException(
                status_code=404, 
                detail=f"No {bureau} reports found. Available bureaus: equifax, transunion, experian"
            )
        
        random_id = random.choice(list(filtered_reports.keys()))
        return {
            "report_id": random_id,
            "report": filtered_reports[random_id],
            "message": f"Random {bureau.title()} report"
        }
    
    # Get any random report
    random_id = random.choice(list(credit_reports_db.keys()))
    report = credit_reports_db[random_id]
    
    return {
        "report_id": random_id,
        "report": report,
        "message": f"Random {report.get('bureau', 'unknown')} report"
    }

@app.get("/api/reports/random/simple")
async def get_random_report_simple(bureau: Optional[str] = None):
    """
    Get a random report ID only (lightweight)
    
    - **bureau**: Optional - Filter by bureau (equifax, transunion, experian)
    """
    if not credit_reports_db:
        raise HTTPException(status_code=404, detail="No reports available")
    
    if bureau:
        filtered_reports = [
            rid for rid, report in credit_reports_db.items()
            if report.get("bureau", "").lower() == bureau.lower()
        ]
        
        if not filtered_reports:
            raise HTTPException(status_code=404, detail=f"No {bureau} reports found")
        
        random_id = random.choice(filtered_reports)
    else:
        random_id = random.choice(list(credit_reports_db.keys()))
    
    report = credit_reports_db[random_id]
    
    return {
        "report_id": random_id,
        "bureau": report.get("bureau"),
        "generated_date": report.get("generatedDate"),
        "credit_profile": report.get("creditProfile"),
        "url": f"/api/reports/{random_id}"
    }

@app.get("/api/reports/random/batch")
async def get_random_reports_batch(
    count: int = Query(10, ge=1, le=100),
    bureau: Optional[str] = None
):
    """
    Get multiple random report IDs
    
    - **count**: Number of random reports (1-100)
    - **bureau**: Optional - Filter by bureau
    """
    if not credit_reports_db:
        raise HTTPException(status_code=404, detail="No reports available")
    
    if bureau:
        filtered_reports = [
            rid for rid, report in credit_reports_db.items()
            if report.get("bureau", "").lower() == bureau.lower()
        ]
        
        if not filtered_reports:
            raise HTTPException(status_code=404, detail=f"No {bureau} reports found")
        
        available_reports = filtered_reports
    else:
        available_reports = list(credit_reports_db.keys())
    
    # Get random sample (without replacement if possible)
    sample_size = min(count, len(available_reports))
    random_ids = random.sample(available_reports, sample_size)
    
    results = []
    for rid in random_ids:
        report = credit_reports_db[rid]
        results.append({
            "report_id": rid,
            "bureau": report.get("bureau"),
            "generated_date": report.get("generatedDate"),
            "credit_profile": report.get("creditProfile")
        })
    
    return {
        "count": len(results),
        "reports": results
    }

@app.get("/api/reports/bureau/{bureau_name}")
async def get_reports_by_bureau(bureau_name: str):
    """Get all reports for a specific bureau"""
    bureau_reports = [
        {
            "report_id": rid,
            "bureau": report["bureau"],
            "generated_date": report["generatedDate"]
        }
        for rid, report in credit_reports_db.items()
        if report.get("bureau", "").lower() == bureau_name.lower()
    ]
    return {"bureau": bureau_name, "count": len(bureau_reports), "reports": bureau_reports}

@app.get("/api/reports/{report_id}")
async def get_credit_report(report_id: str):
    """Retrieve a credit report by ID"""
    if report_id not in credit_reports_db:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return credit_reports_db[report_id]

@app.get("/api/stats")
async def get_statistics():
    """Get statistics"""
    if not credit_reports_db:
        return {"total_reports": 0}
    
    bureau_counts = {"equifax": 0, "transunion": 0, "experian": 0}
    for report in credit_reports_db.values():
        bureau = report.get("bureau", "").lower()
        if bureau in bureau_counts:
            bureau_counts[bureau] += 1
    
    return {
        "total_reports": len(credit_reports_db),
        "by_bureau": bureau_counts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

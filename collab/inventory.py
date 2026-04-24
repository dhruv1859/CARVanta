"""
CARVanta Collab — Reagent & Inventory Tracker
================================================
Laboratory reagent management, inventory tracking, and
supply chain monitoring for immunotherapy research.

Features:
- Reagent catalog with lot tracking
- Expiration date monitoring and alerts
- Vendor management and ordering
- Antibody validation records
- Cell line authentication tracking
- Equipment calibration scheduling
- Chemical safety data sheets (SDS) linking
- Consumption analytics and forecasting
- Multi-site inventory synchronization
- Cost allocation by project
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.inventory")

# In-memory stores
_REAGENTS: Dict[str, Dict] = {}
_EQUIPMENT: Dict[str, Dict] = {}
_ORDERS: Dict[str, Dict] = {}

# Reagent catalog templates
_REAGENT_CATALOG = {
    "anti_cd3_cd28_beads": {
        "name": "Anti-CD3/CD28 Dynabeads",
        "category": "activation_reagent",
        "vendor": "Thermo Fisher",
        "catalog_number": "11131D",
        "unit": "mL",
        "unit_price_usd": 450,
        "storage_temp": "2-8°C",
        "shelf_life_months": 18,
        "critical": True,
        "car_t_step": "T-cell activation",
    },
    "il2_recombinant": {
        "name": "Recombinant Human IL-2",
        "category": "cytokine",
        "vendor": "PeproTech",
        "catalog_number": "200-02",
        "unit": "μg",
        "unit_price_usd": 180,
        "storage_temp": "-20°C",
        "shelf_life_months": 24,
        "critical": True,
        "car_t_step": "T-cell expansion",
    },
    "lentiviral_vector": {
        "name": "CAR Lentiviral Vector (GMP-grade)",
        "category": "viral_vector",
        "vendor": "In-house / CDMO",
        "catalog_number": "LV-CAR-001",
        "unit": "TU (transducing units)",
        "unit_price_usd": 25000,
        "storage_temp": "-80°C",
        "shelf_life_months": 12,
        "critical": True,
        "car_t_step": "Transduction",
    },
    "cryostor_cs10": {
        "name": "CryoStor CS10 Cryopreservation Medium",
        "category": "cryopreservation",
        "vendor": "BioLife Solutions",
        "catalog_number": "210102",
        "unit": "mL",
        "unit_price_usd": 85,
        "storage_temp": "2-8°C",
        "shelf_life_months": 36,
        "critical": True,
        "car_t_step": "Cryopreservation",
    },
    "anti_cd19_pe": {
        "name": "Anti-human CD19 PE (clone HIB19)",
        "category": "flow_antibody",
        "vendor": "BioLegend",
        "catalog_number": "302208",
        "unit": "test (100 tests)",
        "unit_price_usd": 165,
        "storage_temp": "2-8°C",
        "shelf_life_months": 12,
        "critical": False,
        "car_t_step": "Immunophenotyping",
    },
    "anti_car_idiotype": {
        "name": "Anti-CAR Idiotype Detection Antibody",
        "category": "flow_antibody",
        "vendor": "Custom",
        "catalog_number": "CAR-DET-001",
        "unit": "μg",
        "unit_price_usd": 500,
        "storage_temp": "-20°C",
        "shelf_life_months": 12,
        "critical": True,
        "car_t_step": "CAR detection / Transduction efficiency",
    },
    "ficoll_paque": {
        "name": "Ficoll-Paque PLUS",
        "category": "separation_media",
        "vendor": "Cytiva",
        "catalog_number": "17-1440-03",
        "unit": "mL",
        "unit_price_usd": 120,
        "storage_temp": "15-25°C",
        "shelf_life_months": 24,
        "critical": False,
        "car_t_step": "PBMC isolation",
    },
    "chromium_51": {
        "name": "Sodium Chromate (⁵¹Cr)",
        "category": "radioactive",
        "vendor": "PerkinElmer",
        "catalog_number": "NEZ030S001MC",
        "unit": "mCi",
        "unit_price_usd": 350,
        "storage_temp": "2-8°C",
        "shelf_life_months": 1,
        "critical": False,
        "car_t_step": "Cytotoxicity assay",
    },
}

# Equipment database
_EQUIPMENT_CATALOG = {
    "clinimacs_prodigy": {
        "name": "CliniMACS Prodigy",
        "manufacturer": "Miltenyi Biotec",
        "category": "cell_processing",
        "calibration_interval_days": 180,
        "maintenance_interval_days": 365,
        "cost_usd": 250000,
        "car_t_use": "Automated CAR-T manufacturing (closed system)",
    },
    "greg_bioreactor": {
        "name": "G-Rex 100L Bioreactor",
        "manufacturer": "Wilson Wolf",
        "category": "expansion",
        "calibration_interval_days": 90,
        "maintenance_interval_days": 180,
        "cost_usd": 5000,
        "car_t_use": "T-cell expansion (gas-permeable culture)",
    },
    "flow_cytometer": {
        "name": "BD LSRFortessa X-20",
        "manufacturer": "BD Biosciences",
        "category": "analysis",
        "calibration_interval_days": 7,
        "maintenance_interval_days": 90,
        "cost_usd": 350000,
        "car_t_use": "Immunophenotyping, transduction efficiency, identity",
    },
    "gamma_counter": {
        "name": "Gamma Counter (Wizard2)",
        "manufacturer": "PerkinElmer",
        "category": "analysis",
        "calibration_interval_days": 30,
        "maintenance_interval_days": 365,
        "cost_usd": 45000,
        "car_t_use": "⁵¹Cr-release cytotoxicity assay quantification",
    },
    "cryogenic_freezer": {
        "name": "Controlled-Rate Freezer (CoolCell)",
        "manufacturer": "Corning",
        "category": "cryopreservation",
        "calibration_interval_days": 90,
        "maintenance_interval_days": 365,
        "cost_usd": 2000,
        "car_t_use": "CAR-T product cryopreservation at -1°C/min",
    },
    "ivis_spectrum": {
        "name": "IVIS Spectrum In Vivo Imaging",
        "manufacturer": "PerkinElmer",
        "category": "imaging",
        "calibration_interval_days": 30,
        "maintenance_interval_days": 180,
        "cost_usd": 400000,
        "car_t_use": "Bioluminescence imaging for xenograft monitoring",
    },
}


async def list_reagent_catalog() -> Dict[str, Any]:
    """List all reagents in the catalog."""
    catalog = []
    for key, r in _REAGENT_CATALOG.items():
        catalog.append({"reagent_id": key, **r})
    
    categories = list(set(r["category"] for r in _REAGENT_CATALOG.values()))
    return {"total": len(catalog), "reagents": catalog, "categories": categories}


async def add_reagent_to_inventory(
    reagent_id: str,
    lot_number: str = "",
    quantity: float = 1,
    received_date: Optional[str] = None,
    project_id: str = "default",
) -> Dict[str, Any]:
    """Add a reagent to the lab inventory."""
    template = _REAGENT_CATALOG.get(reagent_id)
    if not template:
        return {"error": f"Unknown reagent: {reagent_id}", "available": list(_REAGENT_CATALOG.keys())}

    inv_id = f"INV-{uuid.uuid4().hex[:8]}"
    recv = datetime.fromisoformat(received_date) if received_date else datetime.utcnow()
    expiry = recv + timedelta(days=template["shelf_life_months"] * 30)

    record = {
        "inventory_id": inv_id,
        "reagent_id": reagent_id,
        **template,
        "lot_number": lot_number or f"LOT-{random.randint(100000, 999999)}",
        "quantity_on_hand": quantity,
        "quantity_unit": template["unit"],
        "received_date": recv.isoformat(),
        "expiration_date": expiry.isoformat(),
        "days_until_expiry": (expiry - datetime.utcnow()).days,
        "expired": expiry < datetime.utcnow(),
        "project_id": project_id,
        "status": "in_stock",
    }

    _REAGENTS[inv_id] = record
    return {"inventory_id": inv_id, "status": "added", "record": record}


async def inventory_status(
    category: Optional[str] = None,
    critical_only: bool = False,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get current inventory status with alerts."""
    if seed:
        random.seed(seed)

    # Simulate inventory if empty
    items = list(_REAGENTS.values())
    if not items:
        for key, r in _REAGENT_CATALOG.items():
            qty = random.randint(0, 20)
            recv = datetime.utcnow() - timedelta(days=random.randint(10, 300))
            exp = recv + timedelta(days=r["shelf_life_months"] * 30)
            items.append({
                "reagent_id": key, "name": r["name"], "category": r["category"],
                "quantity_on_hand": qty, "unit": r["unit"],
                "expiration_date": exp.isoformat(),
                "days_until_expiry": (exp - datetime.utcnow()).days,
                "expired": exp < datetime.utcnow(),
                "critical": r["critical"],
                "status": "expired" if exp < datetime.utcnow() else "low" if qty < 3 else "in_stock",
            })

    if category:
        items = [i for i in items if i.get("category") == category]
    if critical_only:
        items = [i for i in items if i.get("critical")]

    alerts = []
    for item in items:
        if item.get("expired"):
            alerts.append({"type": "expired", "reagent": item["name"], "severity": "critical"})
        elif item.get("days_until_expiry", 999) < 30:
            alerts.append({"type": "expiring_soon", "reagent": item["name"], "days": item["days_until_expiry"], "severity": "warning"})
        if item.get("quantity_on_hand", 0) < 3 and item.get("critical"):
            alerts.append({"type": "low_stock", "reagent": item["name"], "quantity": item["quantity_on_hand"], "severity": "high"})

    return {
        "total_items": len(items),
        "items": items,
        "alerts": alerts,
        "summary": {
            "in_stock": sum(1 for i in items if i.get("status") == "in_stock"),
            "low_stock": sum(1 for i in items if i.get("status") == "low"),
            "expired": sum(1 for i in items if i.get("status") == "expired"),
            "critical_alerts": sum(1 for a in alerts if a["severity"] == "critical"),
        },
    }


async def equipment_status(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get equipment status with calibration alerts."""
    if seed:
        random.seed(seed)

    equipment = []
    for key, eq in _EQUIPMENT_CATALOG.items():
        last_cal = datetime.utcnow() - timedelta(days=random.randint(1, eq["calibration_interval_days"] + 30))
        next_cal = last_cal + timedelta(days=eq["calibration_interval_days"])
        cal_overdue = next_cal < datetime.utcnow()

        last_maint = datetime.utcnow() - timedelta(days=random.randint(1, eq["maintenance_interval_days"]))
        next_maint = last_maint + timedelta(days=eq["maintenance_interval_days"])

        equipment.append({
            "equipment_id": key,
            "name": eq["name"],
            "manufacturer": eq["manufacturer"],
            "category": eq["category"],
            "car_t_use": eq["car_t_use"],
            "calibration": {
                "last": last_cal.strftime("%Y-%m-%d"),
                "next_due": next_cal.strftime("%Y-%m-%d"),
                "overdue": cal_overdue,
                "interval_days": eq["calibration_interval_days"],
            },
            "maintenance": {
                "last": last_maint.strftime("%Y-%m-%d"),
                "next_due": next_maint.strftime("%Y-%m-%d"),
            },
            "status": "needs_calibration" if cal_overdue else "operational",
            "uptime_pct": round(random.uniform(85, 99.9), 1),
        })

    cal_alerts = [e for e in equipment if e["status"] == "needs_calibration"]

    return {
        "total_equipment": len(equipment),
        "equipment": equipment,
        "calibration_alerts": len(cal_alerts),
        "all_calibrated": len(cal_alerts) == 0,
        "total_asset_value_usd": sum(eq["cost_usd"] for eq in _EQUIPMENT_CATALOG.values()),
    }


async def consumption_forecast(
    reagent_id: str = "anti_cd3_cd28_beads",
    forecast_months: int = 6,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Forecast reagent consumption and reorder timing."""
    if seed:
        random.seed(seed)

    template = _REAGENT_CATALOG.get(reagent_id)
    if not template:
        return {"error": f"Unknown reagent: {reagent_id}"}

    monthly_usage = [round(random.uniform(1, 10), 1) for _ in range(6)]
    avg_monthly = round(sum(monthly_usage) / len(monthly_usage), 1)

    forecast = []
    current_stock = random.uniform(5, 30)
    for m in range(forecast_months):
        usage = round(random.gauss(avg_monthly, avg_monthly * 0.2), 1)
        current_stock -= usage
        forecast.append({
            "month": m + 1,
            "projected_usage": usage,
            "projected_stock": round(max(current_stock, 0), 1),
            "reorder_needed": current_stock < avg_monthly,
        })

    reorder_month = next((f["month"] for f in forecast if f["reorder_needed"]), None)

    return {
        "reagent_id": reagent_id,
        "reagent_name": template["name"],
        "historical_monthly_usage": monthly_usage,
        "avg_monthly_consumption": avg_monthly,
        "forecast": forecast,
        "reorder_recommendation": {
            "reorder_by_month": reorder_month,
            "suggested_quantity": round(avg_monthly * 3, 1),
            "estimated_cost_usd": round(avg_monthly * 3 * template["unit_price_usd"], 2),
            "lead_time_weeks": random.randint(1, 6),
        },
    }

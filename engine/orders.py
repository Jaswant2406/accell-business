"""
Order management and activation tracking module for Accel Business Udyam Digital.
Handles order persistence (JSON storage), state machine progression, and activation timeline tracking.
"""

from dataclasses import asdict, dataclass, field
import datetime
import json
from pathlib import Path
import random
import string
from typing import Any, Dict, List, Optional, Tuple

TODAY = datetime.date(2026, 7, 15)
ORDERS_FILE = Path("data/orders.json")


def generate_order_id() -> str:
    """Generate a unique Accel Business order ID, e.g. AB-2026-89421."""
    rand_digits = "".join(random.choices(string.digits, k=5))
    return f"AB-2026-{rand_digits}"


def load_all_orders() -> Dict[str, Dict[str, Any]]:
    """Load orders from local JSON store."""
    if not ORDERS_FILE.exists():
        return {}
    try:
        return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_order(order_data: Dict[str, Any]) -> str:
    """Save or update an order in local JSON store."""
    orders = load_all_orders()
    order_id = order_data.get("order_id") or generate_order_id()
    order_data["order_id"] = order_id
    if "created_at" not in order_data:
        order_data["created_at"] = TODAY.isoformat()
    if "updated_at" not in order_data:
        order_data["updated_at"] = TODAY.isoformat()

    orders[order_id] = order_data
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ORDERS_FILE.write_text(json.dumps(orders, indent=2), encoding="utf-8")
    return order_id


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an order by ID."""
    orders = load_all_orders()
    return orders.get(order_id.strip())


def advance_order_status(order_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Simulate order progression to the next milestone.
    Blocks if KYC is REJECTED or MANUAL REVIEW.
    """
    orders = load_all_orders()
    if order_id not in orders:
        return False, f"Order {order_id} not found", None

    order = orders[order_id]
    current_status = order.get("status", "PLACED")
    kyc_status = order.get("kyc_decision", "PENDING")

    # Milestone order:
    # 1. PLACED -> 2. KYC_VERIFIED -> 3. SURVEY_SCHEDULED -> 4. INSTALLATION_SCHEDULED -> 5. ACTIVATED

    if current_status == "PLACED":
        if kyc_status == "REJECTED":
            return False, "Cannot advance order: KYC verification was REJECTED due to compliance mismatch.", order
        elif kyc_status in ["MANUAL REVIEW", "PENDING"]:
            return False, "Cannot advance order: KYC is currently under MANUAL REVIEW. Telecommunications regulations mandate KYC clearance before site survey.", order
        else:
            order["status"] = "SURVEY_SCHEDULED"
            order["timeline"].append({
                "step": "Site Feasibility & Survey Scheduled",
                "date": (TODAY + datetime.timedelta(days=1)).isoformat(),
                "status": "COMPLETED",
                "notes": "Field engineer assigned for physical fiber termination survey."
            })
            save_order(order)
            return True, "Advanced to Site Survey Scheduled", order

    elif current_status == "SURVEY_SCHEDULED":
        order["status"] = "INSTALLATION_SCHEDULED"
        order["timeline"].append({
            "step": "Hardware Dispatched & Installation Scheduled",
            "date": (TODAY + datetime.timedelta(days=3)).isoformat(),
            "status": "COMPLETED",
            "notes": "Enterprise router and CPE dispatched; technician visit booked."
        })
        save_order(order)
        return True, "Advanced to Installation Scheduled", order

    elif current_status == "INSTALLATION_SCHEDULED":
        order["status"] = "ACTIVATED"
        max_days = order.get("quote", {}).get("max_install_days", 7)
        order["timeline"].append({
            "step": "Service Live & SLA Monitoring Active",
            "date": (TODAY + datetime.timedelta(days=max_days)).isoformat(),
            "status": "COMPLETED",
            "notes": "Circuits tested and live. IP assigned and SLA monitoring engaged."
        })
        save_order(order)
        return True, "Service is now fully ACTIVATED!", order

    elif current_status == "ACTIVATED":
        return True, "Order is already fully ACTIVATED and in operational state.", order

    return False, "Unknown order status", order


def create_new_order_record(
    company_name: str,
    contact_person: str,
    phone: str,
    email: str,
    city: str,
    quote_data: Dict[str, Any],
    kyc_result_data: Optional[Dict[str, Any]] = None,
    payment_method: str = "Corporate NetBanking (Auto-Debit Mandate)",
) -> Dict[str, Any]:
    """Create a structured order dictionary with initial milestones."""
    order_id = generate_order_id()
    kyc_decision = kyc_result_data.get("decision", "APPROVED") if kyc_result_data else "APPROVED"
    max_install = quote_data.get("max_install_days", 7)
    target_activation = TODAY + datetime.timedelta(days=max_install)

    timeline = [
        {
            "step": "Order Placed & Mandate Registered",
            "date": TODAY.isoformat(),
            "status": "COMPLETED",
            "notes": f"Contract duration: {quote_data.get('contract_months', 12)} months. First-month payable: ₹{quote_data.get('first_month_payable', 0):,}.",
        }
    ]

    if kyc_decision == "APPROVED":
        timeline.append({
            "step": "Smart KYC Verification",
            "date": TODAY.isoformat(),
            "status": "COMPLETED",
            "notes": "All statutory documents verified against official GSTN & Udyam registries.",
        })
        status = "PLACED"
    elif kyc_decision == "MANUAL REVIEW":
        timeline.append({
            "step": "Smart KYC Verification",
            "date": TODAY.isoformat(),
            "status": "UNDER_REVIEW",
            "notes": "Document OCR requires manual desk inspection before installation can proceed.",
        })
        status = "PLACED"
    else:
        timeline.append({
            "step": "Smart KYC Verification",
            "date": TODAY.isoformat(),
            "status": "REJECTED",
            "notes": "Compliance checks failed; order is held pending re-submission.",
        })
        status = "PLACED"

    timeline.append({
        "step": "Site Feasibility & Survey",
        "date": (TODAY + datetime.timedelta(days=1)).isoformat(),
        "status": "PENDING",
        "notes": "Physical fiber termination path check.",
    })
    timeline.append({
        "step": "Hardware Installation & Termination",
        "date": (TODAY + datetime.timedelta(days=max(2, max_install - 2))).isoformat(),
        "status": "PENDING",
        "notes": "Technician on-site CPE provisioning and circuit splicing.",
    })
    timeline.append({
        "step": "Service Activation & Billing Start",
        "date": target_activation.isoformat(),
        "status": "PENDING",
        "notes": f"Target live date within SLA turnaround ({max_install} business days).",
    })

    order_record = {
        "order_id": order_id,
        "company_name": company_name,
        "contact_person": contact_person,
        "phone": phone,
        "email": email,
        "city": city,
        "status": status,
        "kyc_decision": kyc_decision,
        "kyc_details": kyc_result_data,
        "payment_method": payment_method,
        "quote": quote_data,
        "created_at": TODAY.isoformat(),
        "target_activation_date": target_activation.isoformat(),
        "timeline": timeline,
    }

    save_order(order_record)
    return order_record

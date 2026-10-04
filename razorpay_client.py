import hmac
import hashlib
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional

class RazorpayClient:
    def __init__(self, key_id: str = "rzp_live_TjiX5CotSd0Lrk", key_secret: str = "Z67kRRLfcjLXoHcAA1ndrs37"):
        self.key_id = (key_id or "rzp_live_TjiX5CotSd0Lrk").strip()
        self.key_secret = (key_secret or "Z67kRRLfcjLXoHcAA1ndrs37").strip()

    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def create_order(self, amount_in_rupees: int, receipt: str = "", notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates an order on Razorpay using official REST API.
        Amount is converted to paise (1 INR = 100 paise).
        """
        amount_paise = int(amount_in_rupees * 100)
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt or f"rcpt_{amount_in_rupees}",
            "payment_capture": 1,
            "notes": notes or {}
        }

        # If keys are not yet configured, return mock order for sandbox testing
        if not self.is_configured():
            return {
                "mock": True,
                "order_id": f"order_mock_{hash(receipt) & 0xffffffff:08x}",
                "amount": amount_paise,
                "currency": "INR",
                "key_id": "rzp_test_placeholder",
                "message": "Razorpay Key ID/Secret not set in Admin Settings. Please configure Razorpay keys."
            }

        url = "https://api.razorpay.com/v1/orders"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
        
        # HTTP Basic Auth: key_id:key_secret
        auth_str = f"{self.key_id}:{self.key_secret}"
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        req.add_header("Authorization", f"Basic {auth_b64}")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_body = response.read().decode("utf-8")
                order_json = json.loads(res_body)
                return {
                    "mock": False,
                    "order_id": order_json.get("id"),
                    "amount": order_json.get("amount"),
                    "currency": order_json.get("currency", "INR"),
                    "key_id": self.key_id,
                    "receipt": order_json.get("receipt")
                }
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            raise RuntimeError(f"Razorpay Order Error ({e.code}): {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Razorpay: {str(e)}")

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verifies Razorpay HMAC SHA256 signature.
        Cryptographically ensures the payment was genuinely processed by Razorpay.
        """
        if not self.is_configured():
            # In simulation mode (unconfigured keys), accept simulated/mock IDs
            order_lower = razorpay_order_id.lower()
            pay_lower = razorpay_payment_id.lower()
            if any(t in order_lower for t in ["mock", "sim", "test", "order_"]) and any(t in pay_lower for t in ["mock", "sim", "test", "pay_"]):
                return True
            return False

        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        expected_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, razorpay_signature)

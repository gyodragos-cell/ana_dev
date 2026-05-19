"""
Jules API Key Rotator
=====================
Sistem de rotație a API keys pentru acces nelimitat la Jules.

Features:
- Multiple API keys configurabile
- Rotație automată la fiecare N request-uri sau la detectarea rate limit
- Health check pentru fiecare key
- Logging și statistici
- Auto-recovery când un key e blocat

Author: ANA MAX Integration
Date: 2026-05-19
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

KEYS_FILE = Path(r"C:\Users\billy\Desktop\jules\jules-mcp-server-main\.jules_keys.json")


class APIKeyInfo:
    """Informații despre un API key."""
    
    def __init__(self, key: str, name: str = ""):
        self.key = key
        self.name = name or f"Key_{key[-8:]}"
        self.is_active = True
        self.request_count = 0
        self.last_used = None
        self.created_at = datetime.now().isoformat()
        self.rate_limited_until = None
        self.total_requests = 0
        self.total_errors = 0
        self.last_error = None
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "is_active": self.is_active,
            "request_count": self.request_count,
            "last_used": self.last_used,
            "created_at": self.created_at,
            "rate_limited_until": self.rate_limited_until,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "last_error": self.last_error
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "APIKeyInfo":
        key_info = cls(data["key"], data.get("name", ""))
        key_info.is_active = data.get("is_active", True)
        key_info.request_count = data.get("request_count", 0)
        key_info.last_used = data.get("last_used")
        key_info.created_at = data.get("created_at", datetime.now().isoformat())
        key_info.rate_limited_until = data.get("rate_limited_until")
        key_info.total_requests = data.get("total_requests", 0)
        key_info.total_errors = data.get("total_errors", 0)
        key_info.last_error = data.get("last_error")
        return key_info


class JulesAPIKeyRotator:
    """Gestionează rotația API keys pentru Jules."""
    
    def __init__(self, max_requests_per_key: int = 50, rotation_strategy: str = "round_robin"):
        """
        Initializează rotatorul.
        
        Args:
            max_requests_per_key: Numărul maxim de request-uri per key înainte de rotație
            rotation_strategy: 'round_robin', 'least_used', sau 'smart'
        """
        self.max_requests_per_key = max_requests_per_key
        self.rotation_strategy = rotation_strategy
        self.keys: List[APIKeyInfo] = []
        self.current_key_index = 0
        self.lock = False
        
        # Încarcă keys din fișier
        self._load_keys()
    
    def _load_keys(self):
        """Încarcă API keys din fișierul de configurare."""
        if KEYS_FILE.exists():
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.keys = [APIKeyInfo.from_dict(k) for k in data.get("keys", [])]
                    self.current_key_index = data.get("current_index", 0)
                    self.max_requests_per_key = data.get("max_requests", 50)
                    self.rotation_strategy = data.get("strategy", "round_robin")
                logger.info(f"Loaded {len(self.keys)} API keys")
            except Exception as e:
                logger.error(f"Failed to load keys: {e}")
                self.keys = []
    
    def _save_keys(self):
        """Salvează API keys în fișier."""
        try:
            data = {
                "keys": [k.to_dict() for k in self.keys],
                "current_index": self.current_key_index,
                "max_requests": self.max_requests_per_key,
                "strategy": self.rotation_strategy,
                "last_updated": datetime.now().isoformat()
            }
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
    
    def add_key(self, key: str, name: str = "") -> bool:
        """Adaugă un API key nou."""
        # Verifică dacă key-ul există deja
        if any(k.key == key for k in self.keys):
            logger.warning("Key already exists")
            return False
        
        key_info = APIKeyInfo(key, name)
        self.keys.append(key_info)
        self._save_keys()
        logger.info(f"Added new API key: {key_info.name}")
        return True
    
    def remove_key(self, key_index: int) -> bool:
        """Șterge un API key."""
        if 0 <= key_index < len(self.keys):
            removed = self.keys.pop(key_index)
            if self.current_key_index >= len(self.keys):
                self.current_key_index = 0
            self._save_keys()
            logger.info(f"Removed API key: {removed.name}")
            return True
        return False
    
    def get_current_key(self) -> Optional[str]:
        """Obține cheia API curentă (cu rotație automată)."""
        if not self.keys:
            logger.error("No API keys configured")
            return None
        
        # Curăță keys care sunt rate-limited dar perioada a expirat
        now = datetime.now()
        for key in self.keys:
            if key.rate_limited_until:
                limit_time = datetime.fromisoformat(key.rate_limited_until)
                if now > limit_time:
                    key.rate_limited_until = None
                    key.is_active = True
                    logger.info(f"Key {key.name} is active again")
        
        # Găsește un key activ
        active_keys = [k for k in self.keys if k.is_active and not k.rate_limited_until]
        if not active_keys:
            logger.warning("All keys are inactive or rate-limited!")
            return None
        
        # Alege key-ul în funcție de strategie
        if self.rotation_strategy == "round_robin":
            key = self._round_robin_select(active_keys)
        elif self.rotation_strategy == "least_used":
            key = min(active_keys, key=lambda k: k.request_count)
        elif self.rotation_strategy == "smart":
            key = self._smart_select(active_keys)
        else:
            key = active_keys[self.current_key_index % len(active_keys)]
        
        return key.key if key else None
    
    def _round_robin_select(self, active_keys: List[APIKeyInfo]) -> APIKeyInfo:
        """Selecție round-robin."""
        # Găsește indexul key-ului curent în lista de active keys
        current_key = self.keys[self.current_key_index % len(self.keys)]
        if current_key in active_keys:
            return current_key
        
        # Altfel, ia următorul key activ
        for i in range(len(self.keys)):
            idx = (self.current_key_index + i) % len(self.keys)
            if self.keys[idx] in active_keys:
                self.current_key_index = idx
                return self.keys[idx]
        
        return active_keys[0]
    
    def _smart_select(self, active_keys: List[APIKeyInfo]) -> APIKeyInfo:
        """Selecție inteligentă (bazată pe success rate și request count)."""
        # Calculează un scor pentru fiecare key
        scored_keys = []
        for key in active_keys:
            total = key.total_requests
            errors = key.total_errors
            success_rate = 1.0 - (errors / total) if total > 0 else 1.0
            usage_penalty = key.request_count / self.max_requests_per_key
            score = success_rate * 100 - usage_penalty * 10
            scored_keys.append((score, key))
        
        # Alege key-ul cu cel mai mare scor
        return max(scored_keys, key=lambda x: x[0])[1]
    
    def record_request(self, key: str, success: bool = True, error: str = None):
        """Înregistrează un request (pentru tracking)."""
        for key_info in self.keys:
            if key_info.key == key:
                key_info.request_count += 1
                key_info.total_requests += 1
                key_info.last_used = datetime.now().isoformat()
                
                if not success:
                    key_info.total_errors += 1
                    key_info.last_error = error
                    
                    # Verifică dacă e rate limit
                    if error and ("rate limit" in error.lower() or "429" in error):
                        self._handle_rate_limit(key_info)
                
                # Verifică dacă trebuie să facem rotație
                if key_info.request_count >= self.max_requests_per_key:
                    self._rotate_to_next_key(key_info)
                
                self._save_keys()
                break
    
    def _handle_rate_limit(self, key_info: APIKeyInfo):
        """Gestionează rate limit pentru un key."""
        # Blochează key-ul pentru 1 oră
        key_info.rate_limited_until = (datetime.now() + timedelta(hours=1)).isoformat()
        key_info.is_active = False
        logger.warning(f"Key {key_info.name} rate-limited, blocking for 1 hour")
        self._save_keys()
    
    def _rotate_to_next_key(self, current_key: APIKeyInfo):
        """Rotește la următorul key."""
        # Reset request count pentru key-ul curent
        current_key.request_count = 0
        
        # Găsește următorul key activ
        current_idx = self.keys.index(current_key)
        for i in range(1, len(self.keys)):
            next_idx = (current_idx + i) % len(self.keys)
            next_key = self.keys[next_idx]
            if next_key.is_active and not next_key.rate_limited_until:
                self.current_key_index = next_idx
                logger.info(f"Rotated to key: {next_key.name}")
                break
        
        self._save_keys()
    
    def get_stats(self) -> dict:
        """Obține statistici despre utilizarea keys."""
        total_requests = sum(k.total_requests for k in self.keys)
        total_errors = sum(k.total_errors for k in self.keys)
        active_keys = len([k for k in self.keys if k.is_active])
        rate_limited = len([k for k in self.keys if k.rate_limited_until])
        
        return {
            "total_keys": len(self.keys),
            "active_keys": active_keys,
            "rate_limited_keys": rate_limited,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "success_rate": 1.0 - (total_errors / total_requests) if total_requests > 0 else 1.0,
            "current_strategy": self.rotation_strategy,
            "max_requests_per_key": self.max_requests_per_key,
            "keys": [
                {
                    "name": k.name,
                    "is_active": k.is_active,
                    "request_count": k.request_count,
                    "total_requests": k.total_requests,
                    "total_errors": k.total_errors,
                    "success_rate": 1.0 - (k.total_errors / k.total_requests) if k.total_requests > 0 else 1.0
                }
                for k in self.keys
            ]
        }
    
    def reset_all_counts(self):
        """Resetează toate contoarele."""
        for key in self.keys:
            key.request_count = 0
            key.rate_limited_until = None
            key.is_active = True
        self._save_keys()
        logger.info("All key counts reset")
    
    def list_keys(self) -> List[dict]:
        """Listează toate keys (fără a expune cheia completă)."""
        return [
            {
                "index": i,
                "name": k.name,
                "key_preview": f"{k.key[:10]}...{k.key[-8:]}",
                "is_active": k.is_active,
                "request_count": k.request_count,
                "total_requests": k.total_requests,
                "rate_limited_until": k.rate_limited_until
            }
            for i, k in enumerate(self.keys)
        ]


# Singleton instance
_rotator: Optional[JulesAPIKeyRotator] = None


def get_rotator() -> JulesAPIKeyRotator:
    """Obține instanta singleton a rotatorului."""
    global _rotator
    if _rotator is None:
        _rotator = JulesAPIKeyRotator()
    return _rotator


def add_api_key(key: str, name: str = "") -> bool:
    """Adaugă un API key (wrapper convenience)."""
    return get_rotator().add_key(key, name)


def get_next_api_key() -> Optional[str]:
    """Obține următorul API key (wrapper convenience)."""
    return get_rotator().get_current_key()

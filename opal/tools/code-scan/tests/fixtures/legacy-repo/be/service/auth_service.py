"""
@header {
  "module": "auth_service",
  "layer": "service",
  "domain": "auth",
  "description": "JWT 발급 및 검증 처리 (legacy-repo golden fixture)",
  "exports": ["issue_token", "verify_token"],
  "depends": ["user_repo"]
}
"""


def issue_token():
    return "token"


def verify_token(token):
    return token is not None

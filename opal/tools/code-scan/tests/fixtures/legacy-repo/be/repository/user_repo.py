"""
@header {
  "module": "user_repo",
  "layer": "repository",
  "domain": "auth",
  "description": "사용자 조회/저장 리포지토리 (legacy-repo golden fixture)",
  "exports": ["find_user", "save_user"],
  "depends": []
}
"""


def find_user(user_id):
    return None


def save_user(user):
    return user

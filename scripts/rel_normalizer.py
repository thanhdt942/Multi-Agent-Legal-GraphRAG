"""Shared utilities for legal document project."""

import re
import unicodedata


# Mapping from known Vietnamese relationship labels to safe Neo4j relationship types.
RELATIONSHIP_MAP = {
    "Văn bản sửa đổi": "SUA_DOI",
    "Văn bản bổ sung": "BO_SUNG",
    "Văn bản hết hiệu lực": "HET_HIEU_LUC",
    "Văn bản bị hết hiệu lực 1 phần": "BI_HET_HIEU_LUC_1_PHAN",
    "Văn bản bị hết hiệu lực toàn bộ": "BI_HET_HIEU_LUC_TOAN_BO",
    "Văn bản căn cứ": "CAN_CU",
    "Văn bản quy định hết hiệu lực": "QUY_DINH_HET_HIEU_LUC",
    "Văn bản quy định hết hiệu lực 1 phần": "QUY_DINH_HET_HIEU_LUC_1_PHAN",
    "Văn bản hướng dẫn": "HUONG_DAN",
    "Văn bản được hướng dẫn": "DUOC_HUONG_DAN",
    "Văn bản được sửa đổi": "DUOC_SUA_DOI",
    "Văn bản HD, QĐ chi tiết": "HUONG_DAN_QUYET_DINH_CHI_TIET",
    "Văn bản được HD, QĐ chi tiết": "DUOC_HUONG_DAN_QUYET_DINH_CHI_TIET",
    "Văn bản dẫn chiếu": "DAN_CHIEU",
}


def _remove_diacritics(text: str) -> str:
    """Normalize Vietnamese text to ASCII-friendly form."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def normalize_relationship(vn_label: str) -> str:
    """Convert a Vietnamese relationship label to a safe Neo4j relationship type."""
    if vn_label in RELATIONSHIP_MAP:
        return RELATIONSHIP_MAP[vn_label]
    s = _remove_diacritics(vn_label)
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s.upper() or "RELATES_TO"

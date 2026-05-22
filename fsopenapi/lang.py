import os

LANG_ZH_CN = "zhCn"
LANG_ZH_TC = "zhTc"
LANG_EN = "en"

DEFAULT_LANG = LANG_ZH_CN
ALLOWED_LANGS = frozenset({LANG_ZH_CN, LANG_ZH_TC, LANG_EN})

ENV_LANG = "FSOPENAPI_LANG"


def validate_lang(value: str) -> str:
    if value not in ALLOWED_LANGS:
        raise ValueError(
            f"无效 {ENV_LANG}: {value!r}，仅支持: {', '.join(sorted(ALLOWED_LANGS))}"
        )
    return value


def resolve_lang_from_env() -> str:
    raw = os.getenv(ENV_LANG)
    if raw is None or str(raw).strip() == "":
        return DEFAULT_LANG
    return validate_lang(str(raw).strip())


def build_lang_header(lang: str) -> dict:
    return {"X-Lang": lang}
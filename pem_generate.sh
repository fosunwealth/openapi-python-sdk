#!/usr/bin/env bash

set -e

OUT_PRIVATE="${1:-private.pem}"
OUT_PUBLIC="${2:-public.pem}"

# 生成 PKCS#8 私钥
openssl ecparam -name secp384r1 -genkey | openssl pkcs8 -topk8 -nocrypt -out "$OUT_PRIVATE"

# 提取公钥（SubjectPublicKeyInfo）
openssl ec -in "$OUT_PRIVATE" -pubout -out "$OUT_PUBLIC"

# Windows 下 OpenSSL 可能写出 CRLF，统一为 LF
_strip_cr() { [ -f "$1" ] && sed 's/\r$//' "$1" > "$1.tmp" && mv "$1.tmp" "$1"; }
_strip_cr "$OUT_PRIVATE"
_strip_cr "$OUT_PUBLIC"

echo "已导出私钥: $OUT_PRIVATE (PKCS#8)"
echo "已导出公钥: $OUT_PUBLIC (SubjectPublicKeyInfo)"
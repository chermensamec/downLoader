#!/usr/bin/env python3
"""Измерение скорости загрузки по десяти последовательным HTTP-запросам."""

import argparse
import sys
import time
from http.client import HTTPException
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 30


def http_url(value):
    try:
        parts = urlsplit(value)
        if parts.scheme in ("http", "https") and parts.hostname:
            return value
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("укажите полный HTTP(S)-адрес")


def download(url):
    """Вернуть число прочитанных байтов тела ответа и время в секундах."""
    request = Request(url, headers={"Accept-Encoding": "identity"})
    downloaded = 0
    started = time.perf_counter()
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            downloaded += len(chunk)
        # Некоторые серверы обрывают ответ, не вызывая ошибку при чтении блоками.
        content_length = response.headers.get("Content-Length")
        if content_length is not None and downloaded != int(content_length):
            raise OSError("ответ получен не полностью: объём не совпадает с Content-Length")
    return downloaded, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser(
        description="10 последовательных загрузок и измерение средней скорости."
    )
    parser.add_argument("url", type=http_url, help="HTTP(S)-адрес скачиваемого ресурса")
    args = parser.parse_args()

    total_bytes = 0
    total_seconds = 0.0
    for number in range(1, REQUEST_COUNT + 1):
        try:
            downloaded, elapsed = download(args.url)
        except (URLError, OSError, HTTPException, ValueError) as error:
            print(f"Ошибка запроса {number}/{REQUEST_COUNT}: {error}", file=sys.stderr)
            return 1
        total_bytes += downloaded
        total_seconds += elapsed

    print(f"Выполнено запросов: {REQUEST_COUNT}")
    print(f"Среднее время запроса: {total_seconds / REQUEST_COUNT:.3f} с")
    print(f"Скачано всего: {total_bytes} байт ({total_bytes / 1024**2:.3f} МиБ)")
    print(f"Скорость скачивания: {total_bytes / total_seconds / 1024**2:.3f} МиБ/с")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

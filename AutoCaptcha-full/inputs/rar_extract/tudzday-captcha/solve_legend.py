#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CAPTCHA NRO PC — 100% PURE PYTHON (KHÔNG CẦN PIP, KHÔNG CẦN NUMPY/OPENCV/PILLOW!)
Tự động chạy trên MỌI bản Python (kể cả khi venv bị hỏng numpy hoặc không có pip).

Chỉ cần chạy file này 1 lần, nó sẽ TỰ ĐỘNG LÀM HẾT:
1. Tự động xin quyền Administrator để click chuột / bấm phím vào cửa sổ game.
2. Tự động sửa `BepInEx\config\NroPort.Plugin.cfg` (`Bat = true`, `TuDongGui = true`, `ChanBat = false`)
   ở cả `Downloads\Mod-250-PC` lẫn `Desktop\Mod-250-PC`.
3. Tự động sao chép chính nó vào `Mod-250-PC\tudzday-captcha\solve_legend.py` và tạo nút bật
   1 chạm `Bat-Auto-Captcha.bat`.
4. Tự động giải mã ảnh PNG bằng thư viện chuẩn Python (`zlib` + `struct`), xóa gạch che mờ,
   đọc ký hiệu (`@ # $ % A-Z a-z`) + chữ số (`0-9`), tự nhận diện cả mã 5 số lẫn 6 số,
   ghi `outbox\<sha16>.txt` và tự động click 5 nút tròn cam (`1, 3, 5, 7, 9`) + bấm phím số!
"""

import base64
import ctypes
from ctypes import wintypes
import itertools
import json
import math
import os
import re
import shutil
import struct
import sys
import time
import traceback
import zlib
from pathlib import Path

# ==============================================================================
# CẤU HÌNH MẶC ĐỊNH
# ==============================================================================
TARGET_LEN = int(os.environ.get("CAPTCHA_TARGET_LEN", "0"))  # 0 = Tự nhận diện 5 số hoặc 6 số
POLL_INTERVAL_SEC = 0.03

AUTO_INPUT_GAME = os.environ.get("CAPTCHA_AUTO_INPUT", "1") != "0"
AUTO_CLICK_ORANGE_BUTTONS = os.environ.get("CAPTCHA_AUTO_CLICK", "1") != "0"
AUTO_PRESS_NUMBER_KEYS = os.environ.get("CAPTCHA_AUTO_KEYS", "1") != "0"
STEP_DELAY_SEC = float(os.environ.get("CAPTCHA_STEP_DELAY", "0.08"))

ORANGE_BTN_X_PCTS = [0.3529, 0.4321, 0.5123, 0.5916, 0.6728]
ORANGE_BTN_Y_PCT = 0.9015

MOD_ROOTS = [
    Path(r"C:\Users\Tuchuai\Downloads\Mod-250-PC"),
    Path(r"C:\Users\Tuchuai\Desktop\Mod-250-PC"),
]

PALETTE = [
    ("W", (255, 255, 255), (250, 250, 250)),
    ("K", (0, 0, 0),       (10, 10, 10)),
    ("R", (255, 0, 0),     (235, 50, 40)),
    ("Y", (255, 255, 0),   (245, 235, 70)),
    ("B", (0, 0, 255),     (45, 15, 235)),
    ("G", (0, 255, 0),     (100, 230, 95)),
    ("M", (255, 0, 255),   (215, 75, 220)),
]
ORDER = ["W", "K", "R", "Y", "B", "G", "M"]

SPECIAL_SYMBOLS = ["@", "#", "$", "%", "&"]
UPPER_LATIN = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
LOWER_LATIN = [chr(c) for c in range(ord("a"), ord("z") + 1)]
ALL_SYMBOLS = SPECIAL_SYMBOLS + UPPER_LATIN + LOWER_LATIN

XHEIGHT_LOWER = list("acemnorsuvwxz")
TALL_CHARS = SPECIAL_SYMBOLS + UPPER_LATIN + list("bdfhkltpqygj")

ARROW_HEAD_ROWS = [
    ".#..............",
    ".####...........",
    ".######.........",
    "..#######.......",
    "....########....",
    "......########..",
    ".........#######",
    "...........#####",
    "..........######",
    ".........#######",
    ".......#######..",
    "....########....",
    "..#######.......",
    "..#####.........",
    "..##............",
    "................",
]

BUILTIN_DIGIT_BITMAPS = {
    "0": [
        "..########..", ".##########.", "####....####", "####....####",
        "####....####", "####....####", "####....####", "####....####",
        "####....####", "####....####", "####....####", "####....####",
        "####....####", ".##########.", "..########..", "...######...",
    ],
    "1": [
        "....####....", "...#####....", "..######....", "....####....",
        "....####....", "....####....", "....####....", "....####....",
        "....####....", "....####....", "....####....", "....####....",
        "############", "############", "############", "############",
    ],
    "2": [
        "..########..", ".##########.", "####....####", "###.....####",
        "........####", ".......####.", "......####..", ".....####...",
        "....####....", "...####.....", "..####......", ".####.......",
        "############", "############", "############", "############",
    ],
    "3": [
        "..#######...", "###########.", "###########.", "####.######.",
        ".#...######.", "....#######.", "...########.", "...########.",
        "...########.", ".......#####", ".......#####", "##.....#####",
        "############", "###########.", "###########.", ".########...",
    ],
    "4": [
        "......####..", ".....#####..", "....######..", "...#######..",
        "..####.###..", ".####..###..", "####...###..", "####...###..",
        "############", "############", "############", ".......###..",
        ".......###..", ".......###..", ".......###..", ".......###..",
    ],
    "5": [
        ".##########.", ".##########.", ".##########.", ".####.......",
        ".####.......", ".########...", ".#########..", ".##########.",
        ".##....#####", "........####", "........####", "........####",
        "###....#####", "############", "###########.", "..#####.....",
    ],
    "6": [
        "...#######..", "..#########.", ".####...###.", "####........",
        "####........", "####.#####..", "###########.", "############",
        "####....####", "####....####", "####....####", "####....####",
        "####....####", ".###########", "..#########.", "...#######..",
    ],
    "7": [
        "###########.", "############", "############", ".###########",
        ".....######.", ".....######.", ".....#####..", "....######..",
        "....#####...", "...######...", "...######...", "...#####....",
        "..######....", ".######.....", ".######.....", ".#####......",
    ],
    "8": [
        "..########..", ".##########.", "####....####", "####....####",
        "####....####", ".##########.", "..########..", ".##########.",
        "####....####", "####....####", "####....####", "####....####",
        "####....####", ".##########.", "..########..", "...######...",
    ],
    "9": [
        "...#####....", "..########..", "###########.", "####....###.",
        "####....####", "####....####", "####....####", "############",
        ".###########", "...#########", "........####", "........####",
        ".##.....###.", ".##########.", ".########...", "..######....",
    ],
}

PACKED_SYMBOL_TEMPLATES_B64 = "eNrVXUeT7Txu/StfjcPqW1AURVFeOeecQ3nhnMPYHsea/+4rAiAPQFDS7e5xlRdPfN19L0lQDCBwcPA/3/ned37sm//5zo+/nn/0R+Hbb5YQyrffpHDEb7/Zl3L+Zl3D64clrTF/+03MsRZ7LvEs9i30Iud4fiHFnOoX1tcny1LSWeH5q/DH335zNhLDGnsjx+tTy7ZupTWyBmqrxL302st6vH5aX02n8yP7Ei8bIUnWI7/+n5ftbCTuRwBJlhxJknwjSYzlVdV+nL+7kqQO1wNJ9nI2yZL04dpibaT0Rl6tfOeH5NWU5ZShpNrIKe96nN8g2em55rML65LPHuSVi/31vX09u5jraPFzO1sSQaiqmGoLtQenyK9a23PN54uiJ1f6Ks72aGCoBX7ms69Sd+049b72m56q37XH9CzLnqHb9fVht+uzdftsGbpNz1m3qTHpNfaXn2djNOo/LKO+9plFz307O7CnWN/A2eMYTtnS2UJMS/3jXmdFafOl1D9u0HOulz5SQhuJWmOq04om1xbOX2977T/NwFLkS3V216rajKwz/cBeV2m3SJ9sXeL1cTZH/aWBh3rH/rKk0us6yOcylF5Tvednaq+pv7I4z48f5zhzf89h/pG272yJJkh9o+eyqcswnn2M9M7XUMecX99Z1EV3rray82/O51Yn1ErPCBuCbiJW0dew1SEMuU4W2lVkZVITZam7RojnfnMstY1z51j3JThtnD3uYpzD0MWgn9bITdE8z+eMCUsyYqx1RdTJO2mizhcaqVfN52da4Yqx1ybO7x51R8/prHyv04CbON/JT8g7qS+rPui903x8fbntPa8v110nBVjPBTZ13m+3XrSVa+uVrbTuYDSv63MvIegl/RK9doSrp2Jd9h13/zo6+KTZ+Zo7RZ57Hcg98nSC3ZKL1zjudffeawdfryfYFkQCWhfZrGnqOz31nsnF+joz6DTbQivoNfxk24HivvJxUT9T1zB3TQr+W9y3CJ/cCxWp4E8l2C+0Nd6/X1dPoV2ZusgF/619nz8ZcnsF7Scq1BegpVX1O6NMJGHrzK1Mtk8TmXSHtUzhTiYqXn9zZDpf10/J6+INn46aLdEile6mc8qUvMdJwR/hL7y+3jdQmmMiVjszaD1Uzah3lWqijcEr+CP0hXM5tZVLq7C3ArK0NSFv4Jksr3Wf+7btaWpKFl4evKjbwM1lCTtuBrLXoSzn6/lpWE38zuu0CAedAruRrcyLglOVvt7mWEjTOb4cR1Yzb5xdpmjLKPWvtzmKWpCRyW4UVzLhntDWnd5LLmQaNorHMuXirFuS6XxdP9P0ArVdvt5yHgtv6/Y/2b4AdYJoGTa4hRaiLoa9JMw+2b4AdbaTQ/eUu/9RmbxjBWUaX6leP65M7krTL11kOl/Xz8LretBhLZoj/UUBg6gmRtnjUNihoT55n/SK6etyRHvwkfdlckV78JFLmc7X9XPyumiHbGdVDNOzaj9PmFgOus3Wn86dN7Xi/HqcnSJ95z/Pqox6Dx931PRRNwlTkGrknFVUr76KqyseHz1n9eWRLKKqeqeII4vV4R7K4p1VIsv5en6+nVVmf/YKvWs140h59vW2UWidzS267gPFg+9R0a8vK+ksF4U/x++/RwUN4i+0W0z+isf8XvH5J3X4F6XD9epMjzz/ty7nnKarBV3DaAppNZEu4/ysJq3Lxx5p/OmHaooSqwAeYL2H8dwrnnQRjRbzLtY6H3Vxq/dHuXNiF8+x/KVhBbEuRPfKV0VsJqsrKCcsSJVa6AbNn+TvWY2q4D3j9ccECqVqSfQzryXWqJa4ZGiJa+E6TUsflYmtbNcyubsCfZGsNzEmpQmyFCiMFPRJ/p6nJdLr+uVuBXp6ZL5RqEO5b0NPj8w3ClcH+wEK8wOVyduE6XX9Sltd7oVfjot1qTp+PeSkCBufgyG2Ih65GsePao9qRbXgTc4nt+5IJjP3mIqiRFSj/JKPZIvekndhaQ1iu2El/Qdl6sIomaowD2VSorFMvmgXMi2laXu/CpthKv32H2O1TUix0T6Qql3u2KrBWorq2ZDipTglKPYjt8IO4qvuTHVHKPIeoCAl8nVfov12Db0wylNJuRWDOnFUGxsX7O/hYou8gqr5OBVyHG31e1Kk+hEp1mq+pAJlmg6bFJnutVS8ZCJhYunFS5gIBW/wtaDX9WtdOV/yqJyDnfA1uNV15RX6k08MSVo5H6q4LOgL/PVm779XzvM7svAXlCHpQhZRG+u15Lks/AVjruqb36/DVRfvsTTCbTrST/rmmauH7/1robmiW7Ps1JRyaZlQBVxAPbMDi6YKfX1/LNrcLBuUvgM/WXsU+YIuLYKxva7fsGbZnVd2HIrXzhsnf0MNM1X3KDn71AwfVqsUbADVhfoITrNUAirXtv7qFSUd2JVCFfTBR73v63OvE+tB5+mDshCr98b2/XwFvwmmV9eUP/VLtJfdlGLPAQLmTcfulS6us+Ps6qqq6wDJg59pZj57IJNcF1CmK2XcM789k6mkhzKdr+u3+orBkyEVdKHWtVxgScVQcQl0wsrxCXPFOxSUp98OPfkOMrmzaZehO2Tc4rBTkFBcE1V74cKQNTKX4sQcgCIg9Y6ui7KMJk15ixciVOdOTHaKtIa6W+m3YfHADKt4gg8+fIP3lxhH1GWBxuuTVepOygv8IpPL77xjaHtU8HlZgm84eW4uuyvSpbrl79rPC6XFNANlsfrW1wybVpb0Kjvf0u/CW9qUcAQyIMhNPJcTnXf7XncSAv5UcBBVh756Z6aRlaUNrlZ66uaE7nxBg5WgkT5DI+2IJfiAuHb1cU1ThqAI9JTud7gC1Ymz2PZfGcqx/3u9iWD3CVuB3ceOq+6f7+D32qXk1dM8XtZz3epWumhxkVa+i8XkjyA+Y0FdZ6idCrzGuTbihkcr86Y6UMpKkr5IkvCuJMkzetPZuMRwJcr5bn6/3Uj0iqD3XKcRvmGcQIjnolUj5lX0BQHyqF6NCH5D2l+z65aO48F5xJieUwsNW+7K5bGmEbPT+g/LANbvHNNT1/4OK4nX1Z0ArmF6QCYhloc3XRkgVJz+wNhZZO3BnjRuFO8chcoFxsp3HVQtwxoRunVfLe/Czk40G/yH+oXZierAzQb9yWjQMP9hx8MCJKw2cd7f6rUmFfXF5ejgx7WCT/dcpkAA/duqq1GlR8Yx5UqroX4/KiY0gzPWd/1jnwk1XHte668nWL2fDZ2mmjVCRnf6qmIaDdtxqvhg+HTxTb1/4l2fWW9vV4IiOrPWsmmfbB/LoYzA4cPR1KEJ2v74u5Ghvcluj1K310Spe7Z3idYXmwiIViWEErK1UMhEtNR3nydCmF72Jqx9xR8obqOiXCvAi17Jn8or2as7Rz3pQgMjKGcSKUfDc+/GDbl0XDkt8hrVbYeQG3qEvCLXlaltRdKSIwXAwJUU9eKs+19nb90D+ZNZ7/eXnhSFkueZdCWFY/GiV/JnepWY6yDfaNvd/spwBV/Q7XmIOT3TT5cBmgevjH5sM3Q0Dn2P8GYzjUZX4a/EmV3OJ/g/NNsqS/S1MOw+KVdm2z9v3nVwUJtQh36BmK0XOLyWQ7netJOa7Aiq4pm6CE/UpZqr3fjU8TPXixtVA91ZNQQxuJXiiqOnwLBTV/dSG96/6CtgjXcroMEMFWJF4VMfrAD9CW8FNMs44lU0PO/BClgjrACpOCnodXpHHH8FjDjbqMBFPvhmLsy4Av6yvaKmx1BUCtwBPmRHqvVRNAlfKjsMHu6pb2i6tkYTdhI+V2NX7z9W4zmYf6WNpHxDiJdPMBhwJAVBTDBUx0DN/FV5uX2ACRNhQX7YGkRvTXqNQUEU+UG9Hm4GverJ1vdgLxl6Leamc8j/uuk9VRlWzyMkrdap1h48mzYy1E16kap7tkPe1f1E04FL+PQUgudbdaNZhFu4etKw/82Io6t3lPVjxt0W/pPHKj9eG2xK9b19xiwOtfNfPtKvc+j+thlmqn5Pl7Kifrx/1JHR+21VWsiFUPDHBw+4AKrqalPhI5VNuvaZus6x+7uL1V7RvLxSeOXTGiW8Ij1z2xf4k/y8Xu1Sawz6XjSt+4gT86KzIivujoPO6j2FwmTZAcUqQGy/56BUCFK76ncsbYVz7/1+S++jMZTSsP/9DwY1+xl3Fa7Qs4v/0M1sW3QcopkATGxp3Ur8eNGdUJsBWZDaRZGTHAb6qaIb40Qmxo2ynrcEiyKLR9jDBwqQyZipsm3Qxck9L+h1/WMHCxLC1bixlZb7uWLuKc+AoTMwuw8V3WJdOPhsi/buaj1IT+HrFszesJ1bHkNaIsFuuEEOi/XgOvcFva5/csMYs7pYKfzztFBX/+vQv5tr3JUj9KEhQ6FztImh9fgKGVZgmN/En2lDxm3htYLe0H8GOohg1cZ7Mx8fPBN1EUzgG17jyX73ronvCQ6M+vPIzAdY/2dSKNVdvE/u1Qnr5gNyPGJzv0t/93PXP7hImceX3f3M48sufpP+fubWZ01cNMT/0hRApeLl5rRQz8nbmr9FRCCpJypj8HTanDzbKaTwB6X5itgN9aFnq1u896U/18bD8bEnDfu/9u0ldvO4CSleCGARN17znYaGsH+F/q7iiQ22yUOA6WjiyL+sISzcD3JUbQFiYxT+te2aIwLMx2iRgc7DaFVJkJWgiZGLFcM9xZQdvrtOaFUdkcXI0VIrGBTb+VL+rW03+pr8pv2KuZ38y+4XVbg2/zBy5gAJzvRBTjCqsbiWgpFf4wnUi1EPtWJ60qB+79PgL43AVrqO6338vO4J4S7aQUgcNV+Ey9Iee0NYcmgX/6eAbAxlOJdfshK9Xnbzr/27QYABsgAVXoClPIc61WnnyyPda+r1kTXoGc8yjQSzrcxAWsxgM8NqMb9O5dpBy/HbAqzRCsBOU1+AsRV6Ef/RYGATXNNZnKipWAtGuBHPUVyzM5bBU/su0VNyyaRr3RUOTF+PLpBgR70aPhHGk0KN68eEEdK4R1KkORTsP4FOa0A6oUtoBPvNoVqMdDJR3Lg0zGpwV4AmDSvJCjaGicPSGBcyzH126FikFq0jHTg16b5eC+EWyUbihhzG3p9v4b+a6lonANFjrXmNnT6PuOo6otZAtbrR19P+OkaraIslemUQZDZgRhc2/3Xdud3HVJdT02P5ClAaiVvv8QBZAjXX7zIAaGf4XOs4VDiroxPF/LfPPCI4+xG2hb2jinrAay7PMGGkv1Hse2hUejLPuyJeWPMUVVrUw37KXXKMXKDOABX2JDJ4ZLjSPlEccxxpwbJ1NpuhFnoNP6qDFhE3Iu+5t8ODs6ywf+twzGb8qOcSK8Lf51shsJVyfXWecrDnSptKqBGkr717DUjuWcF8e2Fqk2onJ/bIWPVzGlF9ZLc+1zb2iLDgaog13J77VulEy9mNmEmeSJR9RFYKgViKDI/mrFCV5voag/Q/d47S5djqYXGQpbvUYNOXBgVUpRyWohyzqg0SY+E4HY+idN9oqEpqbayB6DsjRJVZLgfilEwXnKvZ4Vytr4U5VwMbMdgTuWTfea0acTlXNaMrvxePopYMHroRCkaqilcmOlXWAEKsAJ+tGujbjJKXLqN17l206cZK+kheHO3fR4Ja5o5NNba5U+3Wl29YcGMuKAdHXOVguWPRI1cPNZYjZubbKFRrjeKm4jWz6rm3EzCkLAnlWBpRqhgMuIl+sDPvYxRE8VKox3GcWDszxTEFLq+PDJanTt72Q4aMlZxc548IIyY7wdY8Z3znprXwGq9Ey6rOfFJwUAqqup43xOzal8ur6rqN1zHeIZRXjJEkw16oiNYrGresSHBLCibgjHQDpu2FvZN6TUy99EzqbkxO+Kj4e8UwTX1ORViBXxV3XY29isSuu1Vq4A3vEVsOna2Xj8WodSTh7F2zCYMj1g8kGdZUw9RL5uwNfTy6MUs4e8toIjoaKTA/FdMwXXN6f+lJg9wqcn+/xpzMc1ltzaAD0chKDTnomkVP3HsIzw6tqJozmVbpDYXeNxpvNefO+neIexAQe2t32RQ5spF37LPU3H9/V7PiRl5spMRa3WFrXVikqZCGWLefai0k9uTXzaLtVPUTGxqTCfcAxh5FFX1Q5XXmcxhnnepbXLKxz7HeqwZlsfAv7PPA55xIz6LNu1ty6cqxXVU7Gmeh2qo1SrXA5gzsyBPW5bXO7j2HYFmXQ2lc0XWgpfauwlxWjEbwy4rHa6SqmGzCEJ3D+2/qVnT6Dd+oyAfXeLVl8FY7Eju8Gegw+4+GGN7a4ZSCtXEMqtfY39o28XsLcAK26pL4QfMG7ZDZ7+7oukDHFC+7VjfOB6zWsGWzL62q55FO9pOaPzW27NfRCtEQHBJCpqV1r1TwhCDaWmiFRs7znWgh0pJEBn0CJ4Rt7yRPqoHXO6U7HQFXqi5T2XGqHVStF1K9XjcL6jpNCZFA8WWT8il3gr2TY69LvVLu1Yx+fsaJYFhJb+HCHSLtO0ARmiBJWlAiKD5xv++d65vfRbrg+r6lLBeu75X4BhvXd8YmyBx8qtnURDnSFWM5R6ptBDmmSwtNzCZCvZu/KmBnT11vq7CuF7YzUQBO3TDQ6jVW36nKORxWd5+Nep3VnRjXN7a0MfeHPuQEbkE8uWtuA987H0hNXsigdr5ifg2VtDIWOSbGE5Qq34i7oW4dsQgTMnc9dG238bmvVQtMbuWKZZ2j1goaFOjorDpBWQD1z17+Dg+hm1z9BXpjkyLpW/iErnvMQTqJMtuVzlTN0c8UiVnXpNX0LSs888FjmoXQI7XY1KeinTkSWtV8GB+NWOCozwQ5tn1uPQeATYNsqKM52LBROl6ACn7wfBuuCNPzN5jgMToVDbGGXYdG3BLBt8M6aGetwgkCWtACN6hoBDds96DbXVYkt/sRvSZ0Q7Sat5LGJuoS72G3+9gER16CCY9d67VyvoWsKgVI5lwKZWAVoeODC42LbPY2LiKTgB1QpLJkKwOEqSTkl4kBRFHM/LSem1JCpo+6GGjCdpc13REZzrKgIBlt54d2FUUNw2LbPx3ie1JmSQzF61M2Nz+6zDZ2gDYYQTHY9to3eirADYWUw181rTtXr3xRxfG7X5JIbSUny77mUvxrl1fjnNxiwx7owk0l0LM66OKIF6kEoCXg6AxPkxbcsa2rjdaMnCaMaHiI5onAl9NeIH5msG75dPEoB0So3nOc5b7alPVJr+ZEeHMpCvBOVTwtCkCaCqrutIdo6HqDqDAx0Bo7r5IVg6+yALCk41TmejZAr5+yZHwdpybVKI5pvV1wIZsVJW7B+5MmCAGMYnMuhYgZTrZZMoTexJK1LUWveBSjxR1bOcK8EXLYpcX4y5JmKoN3emAimJbUYd7EtpbkMs+kaVxq3/Vov1jzbV6KNVu2CQ/OqdnRURLL9T0pCoh+9LoMo3i30LaQ9OWxJCmNkjjxhcr3qgk+0n2ukPREjhWv/LRj8Rpfp3KwxbdThS2GZ0tHl5SRlQz8KtM5G/zuQ8ijzRHCR28P/VQRWZLcCJYNHFqxaUN999mi5cYYW9DBvMVhETxQwzLb9BbNbsIOPK0PKi1t0KhGQQzHdGst3jVk6OKsBFjQUNnjs9ap4pR0kpNY6qWgn/PE8O8f6av6yNG/rkmsJ+lUzDn/AEWlyfyOJ+lUpslobui6YAwN+JrU32e6i0J/td3EDRXQmonTEl+uFPmgfk0zyRSdVwHNlK4g4wHQBjWmMiGGnEkzaWTpSNifsVp+z/TI+v3W7dFaS+5QdM2cAWG/aKbq90VbedF+9PJm5bK/9H1fx4bm0P1B1z1nDWpTk/fIJteijpvtetVF1yNGtWhfsgY0qAufFIbDg6aj+8n2BY83/VGOoduUPQ9yDKUjW1XZlUje+Jr9oF7MzYlrj13KsixyCpN0P/3KtcdHEljFvoDfa4llHO8C/iuaFiDBuoQGoxG/Rknj/WfrMPMuBlywWqCJI0ZT7Iun2LeMRdQwLkC+ZmOns2cXKoMdQnSOqNjs8Kx3WoBnP0RZsUWpdBPa8NGWYrcVOLMG4oXI/auWopIkL+nxStdx8hD74ax3fjU22Oh2obvr/eqTrn3orRRhiuPoXcrumIJ3suATHYR8lFw+/T1kjbOu6Hip5zEx9QQRLXvoeozJu5HTk4yI41ONCldNpj9YXoSZVVUP8S9e1SahVbfFCX5V9PStZwts1/RDcjVFS356f4dG47lYFI6hjZ4QZo9WHVF0baYNtIskZW7QGRHLkCFBePJHOdKUkt8z8Fy20W70lnZO2eZMG2u8yMmVb3JyXWWpHFIYTO63kqJnnpNrnl/Mu6dLAkq83/Jt4yAomrThSpJm9/RJG4ZY61qOo0zacOQI6p5eel6PPm234TLt3KLnUoAdrK0PzITRJ+3h0+LDPf3n9T1d9icwf9It+jjgME20gbQLOjnydpa1SHzjeEmX3Sk0YyFVz5b7nlaQbjF8w058I1m7TbLufko/p1PWxH3r63Fel7kQ2tmC99tt4J25jAA352Kzw8fhgq4KFVr6hFfajW94TEv9TnjT16TFW9jGoO+weJVVwY3gqnIzMijrh1JMljgZYjeIUiy3lkN68WgHNJu6BO/GRE5rbY3fYEbT8mkmr9iN8qGpzaMrnphMm3GGPkSrYOFl44mg+s6rTEV0q5R+hLRo1Kb94THeivs3GvS8Vk0Ic3Y03NesSh1fGE3Qg7FY6RCGpzQnXC05jBXQNpULOedRmtBNtU9/FSuLG0r6A2WMIVvzPauQhQBcPZ9SPSmEl1JIbWUQ25o1H1KbXcsx+uAHZ/8IYAD4o3n02WuySi4Ucpxa9okwBPMzbpfuVoQApgK5hPQUX1ogcw27yBP6gcxeHQK4UoFsCzpSITUcjM0H6TAQyN5FlSJZwNuV0t6VwvOevpWqk1S4L07VyXFV01SddasEyE7dOdv2OQxoD4cgcYXhL9q7rcLqmKpMb6uSI8gXJJUYolNUwF3r5LR6GktkVjf+u2hgOb0687B1ev20eUUj3Ik7c17uLF7NuMl2PokPIGWCQyyoiMlohlr1rICPBJ5bMco6DegsnwsZz/isHDVPZdVP247YGFW5EaIsPYeR1o+uNM+iiIzAl9TtwBFszqoVnSlJk5oo7EY8lq0Xa9gOsIWyLZF/omSp8gWltHQ1b50neWVGK84V6yd5xZZaktaW63VwwhjNs3D+RZaoGi0OIiMLSQUXKpQTv0J5oc3r52ie0ckh66SSHd4Q2V15m2xUQBiVv2q+R8HIKykuhRF7Pkrh6Yaw2hO/UKcJ9eqv5Jipn78MlISiqk0MXjMbHptKAR2ocrzteNpH196lbGJjzXRGkRGsWC/TEyujesImh+4c7QWC5h8977xAqvbnNt43ikny3P+z1MMPuoh28jm3azf3a3jX8x4qA6xj0wdHk26BXBwDHMWBJF0INnhotKVbN3KNe5rLJnwdrhvoV8yBjraeCpbfa15asV0yY0EzXITQsvmcuXJPLaserBTdNjMlHRQKcxR5tnpV9Uy4IihzAt+u5Fmw4RRtPR0IG2vsH6qoLaaFjU1LbgHNIAkk/y3exPIbEFk0pwvIEsnyR8yZkgZpjUvUaHA3u+yQLlnllSaGHJtX2uMo0SyYz1NXS7Fz1lpo6arBpnGFIbGp4alX5JH8YrjYKHCBi7TTK+RCnedsfcwjD75qZqW4n8HzvdEsinlsbVQbljjaqQwZ0sKWUm6M/StQb66RIxyIuuhctNJM4tPokCz0uQngy5HFlpzqolt7tCgc5796sfR5hdZOMRECX7c48yrFTUZSFQ8Kv+IihQsrslSM5ukFCmmGNR+yG4/1q9ytsvZVBuwhETbVvoEsbEyOAogCjxgXSsu2zdCGyJmDJIGQkkVIIFkWSYad0CmWizUjGxZUL6F3jqRofiyvN6594JCN65KhYHZcIckNARJ6X+X11gm9exDUaxoInWnohUSnUcwysxLQHt+M/VyQbdZmKJ9akTmYQVj0VDsXL6i1o8dvHWKhle2FHEgUpdb9Igtpj/XIrWuAUVeU51V8pFMrcrMbF44e49zqK0IkPBG2iqCidkY1/tfe8RUnp8Bc5KOfyvg/b13F80Tktonmxp020TzFR/ikFClNHN5toDSg+yKdunHozaRwHcVv54dPA0T5Jtf9h/LDh8vkqzNHMffvDB6LUIgI5r3cSDJvYwwje0OOnAZAN7ShPFk6Fo6LIU/4I0D3EMunXv1kWTwAdP+6B+hWpLroNJaIqjswkmDXfZRXTnpPkWtEf1qlizdPvLr4KC8JHtfZuBxotUYppm3E55lblBalIbp14JaT2d7Gb6Vwi8Y3eKxLdHqcYZs/gvy6FYZ/+Rzi6SK/xpbC6KnNodzBw+a01mkkm3W9+h8FgEWVwst3NbNfJLtIrlsE24im9DjFR/S3Uz0YwmjN/0Z3ePU9gWikcpQtangl9Cfh6G4bVVXZxIlqA34163dME8c/Owagakii2h2Dft3Pug38Vd3TTKbQMfslb07EUKlCWZy4uMYu3gjEkjD+qjuICo/zx2Ls/T7wiE1qV3RysVxBLD5QO7AV00h2bO9F5eCNOZo3mlyrSzRecZ1AOC15FnzT8A9JH/v0Lrdo7kqgBZAXzE4VqJuYAkweQ3mr9ZqeJzUfgHnyIocQc9WSDnYXYTdVncvzN3VUBZ6XGDtN93AMYN15wqcRtlIBq8NRrAIQ6CgW9FYZ8mwrd7f2OI1k925gsxvcZA9i1UhZ46XzzD+Fr9Bb1Ir4fnJAr9kafefZEBSt46kAU6aDs5oH0/eaQTiW39IQe7TPwsDEHyWiHE64snaeScSVjgsvaUD8aSdkez86elHPeEUPchtGzQNu0mJYr1m4gW0dGcMhePi1POUYvXOeIHP/2QFx5T2YGi/iAfvR9APOvaxcZ0fR7h5a+7+lkks5AVV5aTAaIMtaYsDuJx1+qk64BZJs4JWYtpOR1grjxnSaX74GlzC7PWoNcu3kTsJlu8puXeKmU+Kkaa7RGY6ZA1zQcQhAEW1WVvkDjjypv8FHlu4+UX5JZuFMzC6jDijv1jtJErxnyIEQN8h/WhA0dJEr2A9dT3hQS8BDDpr+UPhrMMZfQB3x5sauqHWjJUtvB6amD9jzCJDqxAKcJIcB9eLWUjRadOJJvyPbzZc40GJitgUkX2xnlwRvpzRcaqXvUv1qmd9ouf52O6qb3xRSmNP0m/m/B//06Fe2PiWpnVlWL5B60xwpzl2j+5Zp0cR30Zgj0LFBO/bcZtoEafroqXGoyjjwFUhKjYH+ihqNl3KLt1jMtpd2/Jm6UDk1Wsikrsd76CtaDMiu2mfCtF6AxrXHoVxeQKuKeoPXFxdkBorkub5+R9YX+b0wjGEMjb7A+7NfALhQeCfE3ps2okcvEMe4f6XFsD4xMmyOyAaI6HYB9oOCCYXbnDZN9oYcqiBbcDT4nq+1M0+gM36ofLq45+f4ZMKWMW9L9E26W74beq/aSZz+TBjPLWzegt+KF6h/9NR1NlRKhzJ0CRy2JCXB9L6q5/JiYiXsYjCxF5jBJXa8r6d0nIv/d+3h2pdOqPf4pK07QthMQQGd9q2MkZKbtyTFVqnjLKqhh2qGtLQqaSxkP+O4CcWQqMPe2uhjFBQX3HeQAFsYc6PhbX4g15AWJEQa4doihM1/q1KeqSbYeQEzUZmRTGY85A2k5wjNt2QvnuOFs/2sJjcNcSjO0qhwuhB1HHs7zWJyKDq5PI6euoJMe8ONB8k6DHNGHJIsjTmKVh2ZoGpmo1AzWEGsEV3byc0LBOGQbKzb8BTNekFtX2dTIo89h9cAm28dzY7ij5TKRBbp7zVXMZ1FkQEZNOteRXVC5q1m580bXZY2Wg+BnNZEFSxA4VownHfUWdpaqha3MytRBxWtIe91DtXoTAFSCXkc3WOJeL03FlzNSGR5CeFmcKoKOlHuJtJ2EqtRpPjLhb8VEC+xONJQlSbtEYtBxcJcxJlZ0FXhtaPJ9SvVqpvDSRJ1tGLM4TTLp6QThV+mu9pWduClWe6maSMqDdU5sXOcycDVbxUst9d7DPP+ER7qoFUY+jzXtOenNkvJN2zvE1a/blkqxudYvT5mMrVA/d+2TY3ZTsiphTA7a9Dgx7XS/K5MVhyGGxFXXYOcdZ2v223MKnkWmX2zPBNxORMusd6LkTTg97V3mCkMiGiYjJqwg+WgyWP3FWy5bH6r3xyjOIQnKASnYqwzieONrISCekvJixBBCC1u7sMxgdzmFB4li6kFQftxG7xpqoClNXo5pbzKaY/k49owfx8RM0K1IxW9Y2P1hqi34IWo6FRT0WYOm2f1WsxZiwtzkjts6SHd/JJIqVEvcUhASTTAHLKkeWAdDBe9OapdIrFs7Ug1rGoXJrky0pK0mzfHSHBAD+pgGG0o+ZWOFrlGuC3XfiyBTBKBFBfMwqJa8IeFHEAjYusPmq4c5b2v2fpXQX9VuXAnlih2JWtLlNWVSUnm/GqQIjEntxF4oqfaVN+uH6XL7S7ci9hgHWYs1JkIY2CsHXid9cT0rVAuaYtV7VMf7iO4FT+0o2mNnpV35kjNQ7+f2tNQHdTh5eQjldHuewE4tmcmK4Pi3nO35G8HU5wFL+meyeln6sa+bqC4kwpcOtUJ5MW9iN6MusYcTAb1qpOidp6OMdKyV90V4T9sK3DvyRYpf3GztbVwfNq7JHzdMaPv1gM/r7Vnv+PkdCrxneTt6/R3aSAihFzLPdyXYsWSDuPCjeGC9s6vFsQ/zGpQfZ7XayinejeLMlmPBnbL1+cz3CkHQBjoEyb5G22KQY/TbmSE7MNr+z2Gx6kopmXMCaBGBTptkk4qz8BmcwToitmHiM5McsL0GdHRP6rfnFMHaOuUHUGx4g0Vw1gMWy65Pqlm9sQApulPXMdpPQoLp1DNJimC3J7Yj5WVp6crunGCPGq5luhwLk4kD4WYkAt8OYA1XXJ11S9nH2ijiLSraVpnhvVQYTq9+mFTSNBAKmcYj8K6dHso5JqH/nM4Qk9s2Si484x12uD70tacmraJllUgqJaYd7YqF/kmXb2+dPuSUDPDC8mQKlklCVe3DQFLKIyFIm4H5tiAEdARM+gAN+CsGSFsnTfjvxiV8nkZ8tZycpBYoC1sZDGZJdTL2w4+TkILLmF91UQm2OWtTS5+G/LmFp3iPNg2zoX+pyrEeGQYKf0Ap7yROlFvvwWixVz7xSgRzRBLnCB/Mqek5GtEKTrVsHKXpEdRxqWnIpt3u2c9lw1wG/o92rlVppWxbrgQYYIzpdNNUbdZpd4I2qCqntAAXUHu6lY5N9AiNNSqO5/DZd2xXs5y36ZmA01PzDW2qn5P4mq3MbmMM01Uvwvu9iMDhQ4LhhHnHORkgwB4ED9p+6+GSdaQtdFImNUwHnhae2qXT7RzebWfi/TPgFIn6FfJ/ioJKWteQI9dn2B67WSe+lTHRgTzfVDCsMrPLymaTcEOziUmc/zrcJI9WwBM0x8ARjITZERPITDWb6MMcsSYw1yOAJiolh16zKXgn9CpJZq7znQgCe+LhVF5CYjtyzjIIon5smeyZIiWBlk0oArxTh4qaUjTkGbxGVi7IhRDQSQAR9JcTF+GifrWqbqHJo48pOvI4SZnRn8Rgzvbm1iQqVdN3tlb2EoL8W5CxC1quDGy/vx5cwPx1ZR0vY5E3MWruseRUw/pqdCuoc6gLcOl1yjBlKTQoF9V0dSPrWnAyryAZFQFCXxhu1aHWoGoAngWv0oyaqs34MVzaGetolhaol/z1hNkTvtqD0xWwo/dDVfvD91fRLH6RV6iySbqQAU6lxjqU/nIOlAEfbL4LpR97LbaIbEcPrFah7Nt0Wxg+5p1vtbR7S2Werh8OiBKg6mCBKgW/YxuAi7GPL+0AP9C3X9HeG+LEvfoRTVEdz/iRQomPGzNfVPiwj1eUSE9YLDlApStGH9iTkI8qhZwrnOI88BdCunoZNjwwqGRoc6J3k5bFdgOF8QWEC/7/BEHreHBaQsm0gkLK1Aae3qDAfq4QhzQXy2EyCLbfS6+5qBPW8Hpqtg/XP+DLA6sJsdkSJfNcbvkYXdXdNVWEmqDkxsw48IggmoDbCyA0EeCDomKwBiJZd+QhfXuwO2rsC0SPnGLua4niMOI/CaAScdr41zwf9mBFwExH+g5ok765rTRSGpQSzHpnKNDBs8jlrmbZPT3aIb7XjEMFStbritn5onRfjugXERbHXuTrXXxkZPEdhX6C9vjG9hgY1Fmg+ViYvCeM7e+3UGNZBpdLcYUO/BOGl+NOSf7YyTY1D7ffk6n7u2HPh0jHyXN/b/S10tUU9QtG4/mFAz9p8QyUUj2hLk1dIszxqsnUFO60qWAjLdI4N1muHiuZa6L9aeZC/F+GFVhombOtM09hVEjV1m3jz2/r3HShWDLGsE3EFCU8Yo91znR3ss6F+G4jxjmsFicfKweDj1vsI6mKxNZItg8tGa0RAOUmOidWDHVdl3xYZIms2d5VD/3I+qhrupvKX61nKekK7RW70T1c0/DMOct64HE4+mvP2emZVabtgbo/05asDfMtCWY8VL+dB0kNzHTKlOqADJ6tykOPy7ZLN3yISMt1Q9Pnk/w9OBOUyOtk0Lx9vnUSLvnYZjL3fMtI+042LPnJbb7wkiLi3Uw0iLiUXtVtJGW8Ss52bFhxO7Y53oRKpTHXlhOhv4PGWBjGRMwHQD1we4qC24wXBB/o8jP4ewe1I21gbYt4Gak4TepAq5zDzzJE7A0/Am5ai7UopVBEAMZ/uQWfqWy+aroJEMAjcDX5AcoPGxflh0gDMPxIEGA1ieUcqyGxbD4v58XYOyv151JZBwfAThrNETvRvU9urfrXBF/2y0pgjUc9dvFwUP1OedFLbbaOp6oPTpcoz/8y8pooAp+Z8xS6A83orJV8GxhWUmdFBx3lXmPYwjJ68qD+sFMYu8xLq7+G8JYvZMpY+xZZcqmUaz/NZ2bLjPzrpwV0avzMnpMO7v2Pf3vbnQv9lFvDVuKKELJTZsbaHeNgty+U71YVQI4NPIfCU0RGVBKB6M+Ur0YYTv0VxgL1h71BVFUqtcTwwSD9aHXOBII3KY7xTuqF2mBGNAVcrIDAqFfAN2+rRvC3cZILnnm3r7cGm5UL+gxvf6tH8o4JBzdRa/luerFV062OMHdG8dE5MmNcYo1mnvVaxJChz1H/Z3RYY7qZf3jkBR0GHOndlJusHbwj//9ROuaLuyP6V13WZ/e07wePN7QvR6oMm9pX/8v8zN9Sgeb5Gf6jB7mdfRTmph+vq+M/YMhACB6x4CZ8hJn9FSM35HiSCNxoB5b6aTtB8UgJg2NVPUvSH/FmLdU1oFY/ExrMrDB1/qT5WuXuIwc2Sew5Lu+E6nrsaypcbK3YuM95vzcuOW2RqSIs7ZEjnykJg5IVVgSHbFVozg14PCKSP7t4rKl1sna5auowweFDvrfknJiUWipIvpvE6nMRajv6zXzHALUJbpesmrr4hBQ05wUxb6ddVnorRK3hWlnaQre+RdKuUP+V9NM6atE5p2dIJDD27DP00UCnI5CAq4aa8XuMfPvR561cq7/fzQBiLkYpFezxRcbgK1xxz1H5+oGg3D9x2rIqCl0tKe4APJlzYkqGKqKMY7LQNouIQhly0OGx6u8o5rjVWUa5Z+cJBea+ZRzZvi5LuZNC9MUSab4cjh+uoPBwbMp9O6f4unozDwct63XDOWZcBNTvFu02bxGbl8c5g4y3RHNZzW071AplrQaYvFGMM2SUqiXMWHn1Yx4HPjpiNOKMJ8CxHBKNHWU8UGR1XVRyPNoKP5UQ5NO8yqq85CX8cCH90+y/kv3F7lZrBniaemwNfXLAFo06QVnOFJBtlzPJkYSLPESRzrANXhxEsd6Q6qO0rSkYYJbRITnZQsaCzuXobVwhyF10Z1KgCtydfqINPZmK4wh1b1Xg2ZEGjGkXiuaYb3t7+Mrkc4jub9CarBPc8t3GNICTVy+DI0h9TEtR4+3Usujw6wvXsSMJt44lUMoZqAINN13qIuZZUCkyfMZ/rMmvpUozNRpFRTIPZmoTQkuyINRwOgtewc0MK0uUjdwvZ0TRWoHHI6yaeja15wgDLqUZ5Ec3PdJSrN2upfw0OfWkWnKRbRtcbDIGAJ9cF09j+jgz9+wss87PovogMiIm7pzjvdOTiASwjj1OzL22Kt2Oj+wE71TNTCEjTAENWUQUUaGm8Gk65iCAtSvCJT8mhNEcnjh7ucq/a4HviHMq8xAi13ZgXP2OCbelIGg1gJjBv89VgtMt5DlEg3LokFM8DbgtFfZctcRYXzkx73lKcL8COGyWo1u+CTABv99IbTGAYmjgwvnm6ZQ6XmQ9tjzJ2MK4SX6vQZYzTVyvoQBiFXDfxOHJGTDsnJkH/7iddgkkabqI/DnDng3J6DDBXQ3lsAO1uo15yA1nyvvXzTFwHKsuaOGOvRlJNyYpbNg3Kyh+ODjkeO7GqNnggQxyBNHNrPxKZVvIzJNKH5SAHN5uWCtfUQeIvAfiBWgPRv4+abPm4QfmDRd3BL3336WTARPFuzxo35PnsBqELXX7Hqkna1/ysO7Km0E8pxM+jR9ow7doPX14YS7toF7PgT3IAfHJBJEIgOiarQMxEudqvJfvYwqI7t6CQA/5dQPO5DJekj/w82qUsA+VSQ8viwpWu7z/cDLqbnYNay0PSODyQrBvc+p87dU2GIo1uSBAWL6oiWgVDdKM7bM1oI27QzaOheozkph2eG9rBNkMlME640x92ylUowgw7riaPAiLYbMQmRijXu09CXAgRKXBbKpCh3A2uGi13EWe0SSkS3iEAjbOrOVe3GmauWqcRLLDbPHcFBIxBgIfp2ViT5KhlHFZjGuYGYbwL9zC4xli2iZUsNFxOt7HGJecDoB622jeUhHRgm2OA70UUljK0nXeK1em5L7b7KgEbkBt1aOMHgQ+wC7x8QTOgYqzBio3qx4CASYMlsNT4gfue6wrvi+eqfi1aR6gnqvXajkxe6cpxM37ryj/hOq1bujAeUk2A9dUi9wtfdOjncSFB1rLFdc9Ni/pLn91sZsiaANPJvHk90dT4cVQ8DKHR+j6r06k7HHAFb6XgMr6az3pVx7RCx79gF7WduQBkpIdvNmPHe8FHfGUi6BYZjNRkUWOtmGrU/KLZY8uHicWFq+ohcny3jrresxSLNx8tiI+FA2vHkf9OJgjt+Wjxq3YnKsXScZf1TsoRex8gx3EpzOdqo40T0vmp9a0U1/2PKBEs4qDcwaw5uZZVPUPO6KM6Dmhi+VjoieBrJZb1Ap2LxSk7QEE+L43JvYILWJbcIwGg3pzD0fjxqpo2mGGLP875bgvRkmYfGruAHF8H7Fw25uKooAoueXVq+Gw9vJP7tJ2oNNqXQR06UQY7pHxA5Jg91JFHTKQwlVsoSOSOvYF4qm+5AWlEvs6Hycu/Jp2UMG2xmp2Mtsx9JBBgfcMItheESeR2etJ29t2ZgpsJvNGtAOsDEbk6QbSKEzRxIldDaMw8O5qtM8F8zDFJLtt8QFhy1r6qAJ63v5ADk7UrTzLa9TtMdUbNpJ4YrkDCD6Koj9bYbgoq1KUD1rGufi/Q9L/H5Nyc6nM2GLGT1Arv2e7p7gM7m4MaRClZ5SaK0A43tGxnfFDdCI34tlmXfSf0or2x4dQnZifF/JSshpboLiEnSI33m7eML7nuNI+C5Fecb7rtth+n3FXK8LI04KCpdyDDFREFg7ZX6nF5lzcKQpSLakpTn8aMkObvOI05E/fY1HQhp1PhQCoHj6WiLKGMvQ7rDLdwr1FIGejvMxkUMTG0GueY8AvrK0N575vSD/e4UYbvVvHv87wDU1VBlqPsnw43P+d2J+Xw/gH+Wqz0X+nw1+pbjq9gZtlh2iZchAOnIxqwtLe0sVqjKRYpLiQxmdg0sDnxNwCxLvBAeUD4k7G6MJE90V2eSuWdqVO2ClUFUHa8UGbsKGvbre2Emx6yOJuuIz0dpT1n0HtzzZ4VbFlbDY2HwAMgB3m8YxIAV8x3pwHoOlpCsi+NVQGO1COQbAEsxeojPQjFoOX3E7sTHGA8tiXUZk03hN0oSLjnrQu95CglOH9a1DtHXsGUMNSTvkydGUGLXrNMdyv2RqL/WoUrfUhlvUwQRYLa2ItRp5aaJpP8K5VP9LgyckzDpCFALZbnpiGxMUQEGMnFIXUq6blcrROEgImMNd+gO2BrDOHOlI1OPebs096JtDfmZZhKzdTfmdDHKCxmu3vJc6J4/VWBVhO288kGvdpGu4ToNEgL8hARJGchxjdLEmbEC3N+aDGLNCDFETXuXJsAhILE9tkZnVZ+Tv0zjHLWtMhKjYIWkV20X/p2K9KyaTme5o7UPtqKnNQAuc8L2qNpd+HZhcBEwuJXo0OpPS6d//W5+ULUNs18mLIuhB32ljaV8grFsIG+z6kzded816BKd2YZFjZrWL4TSMRHR7WE0RGds5v2hM2GskmB/cvhruiFc9NkD2anuXP1Gt5mqXv9+xy+uxXjWBmaGCL8H4yeD9WWVHvcq8xDKhWRt8SADN6uFaGJ9lLf870ysDa/vAbKL9Rly7DgHzxial64oH1naykBii+WFXIIbzRgc/GkzaadE9TmtuaOyxu+i9PjJ0es/6PPzRdj8F5hT+GGyg3PhB6sMKXr20USKVrZSBw5Nmyx9///v/C4U9Gk0="


# ==============================================================================
# BỘ GIẢI MÃ ẢNH PNG THUẦN PYTHON (KHÔNG CẦN OPENCV / PILLOW / NUMPY)
# ==============================================================================
def decode_png_pure(file_path):
    """
    Đọc trực tiếp file ảnh PNG 8-bit (RGB, RGBA, Palette, Grayscale) bằng thư viện chuẩn
    `zlib` + `struct` của Python. Trả về (height, width, rgb_rows) trong đó `rgb_rows[y][x] = (r, g, b)`.
    """
    data = Path(file_path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a valid PNG file")

    pos = 8
    width = height = bit_depth = color_type = 0
    palette = []
    idat_chunks = []

    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"PLTE":
            for i in range(0, len(chunk_data), 3):
                palette.append((chunk_data[i], chunk_data[i + 1], chunk_data[i + 2]))
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    raw = zlib.decompress(b"".join(idat_chunks))
    if color_type == 2:
        bpp = 3
    elif color_type == 6:
        bpp = 4
    elif color_type == 3:
        bpp = 1
    elif color_type == 0:
        bpp = 1
    elif color_type == 4:
        bpp = 2
    else:
        bpp = 4

    stride = width * bpp
    recon = bytearray(height * stride)
    in_pos = 0

    for y in range(height):
        filter_type = raw[in_pos]
        in_pos += 1
        row_out = y * stride
        prev_out = (y - 1) * stride

        if filter_type == 0:
            recon[row_out : row_out + stride] = raw[in_pos : in_pos + stride]
        elif filter_type == 1:
            for i in range(stride):
                a = recon[row_out + i - bpp] if i >= bpp else 0
                recon[row_out + i] = (raw[in_pos + i] + a) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                b = recon[prev_out + i] if y > 0 else 0
                recon[row_out + i] = (raw[in_pos + i] + b) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                a = recon[row_out + i - bpp] if i >= bpp else 0
                b = recon[prev_out + i] if y > 0 else 0
                recon[row_out + i] = (raw[in_pos + i] + ((a + b) >> 1)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                a = recon[row_out + i - bpp] if i >= bpp else 0
                b = recon[prev_out + i] if y > 0 else 0
                c = recon[prev_out + i - bpp] if (y > 0 and i >= bpp) else 0
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                recon[row_out + i] = (raw[in_pos + i] + pr) & 0xFF
        in_pos += stride

    rgb_rows = []
    for y in range(height):
        row = []
        base = y * stride
        if color_type == 2:
            for x in range(width):
                idx = base + x * 3
                row.append((recon[idx], recon[idx + 1], recon[idx + 2]))
        elif color_type == 6:
            for x in range(width):
                idx = base + x * 4
                a = recon[idx + 3]
                if a < 128:
                    row.append((114, 114, 114))
                else:
                    row.append((recon[idx], recon[idx + 1], recon[idx + 2]))
        elif color_type == 3:
            for x in range(width):
                p_idx = recon[base + x]
                row.append(palette[p_idx] if p_idx < len(palette) else (0, 0, 0))
        else:
            for x in range(width):
                v = recon[base + x * bpp]
                row.append((v, v, v))
        rgb_rows.append(row)

    return height, width, rgb_rows


# ==============================================================================
# CÁC HÀM XỬ LÝ ẢNH NHỊ PHÂN THUẦN PYTHON (MORPHOLOGY, CONNECTED COMPONENTS, RESIZE)
# ==============================================================================
def zeros_2d(h, w):
    return [[0] * w for _ in range(h)]


def dilate_rect(mask, kw, kh):
    h = len(mask)
    w = len(mask[0]) if h else 0
    rx = kw // 2
    ry = kh // 2
    # Tách 2 chiều: ngang rồi dọc để chạy siêu nhanh O(H*W)
    horiz = zeros_2d(h, w)
    for y in range(h):
        row = mask[y]
        out_r = horiz[y]
        for x in range(w):
            x0 = 0 if x - rx < 0 else x - rx
            x1 = w if x + kw - rx > w else x + kw - rx
            for xi in range(x0, x1):
                if row[xi]:
                    out_r[x] = 1
                    break
    out = zeros_2d(h, w)
    for y in range(h):
        y0 = 0 if y - ry < 0 else y - ry
        y1 = h if y + kh - ry > h else y + kh - ry
        out_r = out[y]
        for x in range(w):
            for yi in range(y0, y1):
                if horiz[yi][x]:
                    out_r[x] = 1
                    break
    return out


def erode_rect(mask, kw, kh):
    h = len(mask)
    w = len(mask[0]) if h else 0
    rx = kw // 2
    ry = kh // 2
    horiz = zeros_2d(h, w)
    for y in range(h):
        row = mask[y]
        out_r = horiz[y]
        for x in range(w):
            if x - rx < 0 or x + kw - rx > w:
                continue
            ok = 1
            for xi in range(x - rx, x + kw - rx):
                if not row[xi]:
                    ok = 0
                    break
            out_r[x] = ok
    out = zeros_2d(h, w)
    for y in range(h):
        if y - ry < 0 or y + kh - ry > h:
            continue
        out_r = out[y]
        for x in range(w):
            ok = 1
            for yi in range(y - ry, y + kh - ry):
                if not horiz[yi][x]:
                    ok = 0
                    break
            out_r[x] = ok
    return out


def morph_open(mask, kw, kh):
    return dilate_rect(erode_rect(mask, kw, kh), kw, kh)


def morph_close(mask, kw, kh):
    return erode_rect(dilate_rect(mask, kw, kh), kw, kh)


def connected_components(mask):
    """
    Tìm các thành phần liên thông (8-connectivity) trên ảnh nhị phân 2D.
    Trả về danh sách: [(x0, y0, w, h, area, x_mean, pixels_list), ...]
    """
    h = len(mask)
    w = len(mask[0]) if h else 0
    visited = [[False] * w for _ in range(h)]
    comps = []

    for y in range(h):
        for x in range(w):
            if mask[y][x] and not visited[y][x]:
                visited[y][x] = True
                q = [(y, x)]
                min_x = max_x = x
                min_y = max_y = y
                sum_x = 0
                idx = 0
                while idx < len(q):
                    cy, cx = q[idx]
                    idx += 1
                    sum_x += cx
                    if cx < min_x: min_x = cx
                    if cx > max_x: max_x = cx
                    if cy < min_y: min_y = cy
                    if cy > max_y: max_y = cy
                    for ny in (cy - 1, cy, cy + 1):
                        if 0 <= ny < h:
                            for nx in (cx - 1, cx, cx + 1):
                                if 0 <= nx < w and not visited[ny][nx] and mask[ny][nx]:
                                    visited[ny][nx] = True
                                    q.append((ny, nx))
                area = len(q)
                comps.append((min_x, min_y, max_x - min_x + 1, max_y - min_y + 1, area, sum_x / float(area), q))
    return comps


def crop_2d(mask, y0, y1, x0, x1):
    return [row[x0:x1] for row in mask[y0:y1]]


def tight_bbox(mask):
    h = len(mask)
    w = len(mask[0]) if h else 0
    min_y, max_y = h, -1
    min_x, max_x = w, -1
    for y in range(h):
        row = mask[y]
        for x in range(w):
            if row[x]:
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                if x < min_x: min_x = x
                if x > max_x: max_x = x
    if max_y < 0:
        return None
    return min_y, max_y + 1, min_x, max_x + 1


def resize_area_binary(mask, out_w, out_h, threshold=0.33):
    in_h = len(mask)
    in_w = len(mask[0]) if in_h else 0
    if in_h == 0 or in_w == 0:
        return zeros_2d(out_h, out_w)
    out = zeros_2d(out_h, out_w)
    for oy in range(out_h):
        y_start = (oy * in_h) / float(out_h)
        y_end = ((oy + 1) * in_h) / float(out_h)
        iy0 = int(math.floor(y_start))
        iy1 = min(in_h - 1, int(math.ceil(y_end)) - 1)
        for ox in range(out_w):
            x_start = (ox * in_w) / float(out_w)
            x_end = ((ox + 1) * in_w) / float(out_w)
            ix0 = int(math.floor(x_start))
            ix1 = min(in_w - 1, int(math.ceil(x_end)) - 1)
            cnt = 0
            tot = 0
            for iy in range(iy0, iy1 + 1):
                for ix in range(ix0, ix1 + 1):
                    tot += 1
                    if mask[iy][ix]:
                        cnt += 1
            if tot > 0 and (cnt / float(tot)) >= threshold:
                out[oy][ox] = 1
    return out


def normalize_symbol_16(crop_mask):
    tb = tight_bbox(crop_mask)
    if tb is None:
        return zeros_2d(16, 16)
    y0, y1, x0, x1 = tb
    sub = crop_2d(crop_mask, y0, y1, x0, x1)
    h = y1 - y0
    w = x1 - x0
    aspect = w / float(h)
    new_h = 14
    if aspect < 0.45:
        new_w = max(2, int(round(new_h * aspect)))
    else:
        new_w = min(14, max(8, int(round(new_h * min(aspect, 1.25)))))
    resized = resize_area_binary(sub, new_w, new_h, threshold=0.32)
    canvas = zeros_2d(16, 16)
    cy0 = (16 - new_h) // 2
    cx0 = (16 - new_w) // 2
    for r in range(new_h):
        for c in range(new_w):
            canvas[cy0 + r][cx0 + c] = resized[r][c]
    return canvas


def unpack_16x16(rows_int):
    out = zeros_2d(16, 16)
    for r, val in enumerate(rows_int):
        for c in range(16):
            if (val >> (15 - c)) & 1:
                out[r][c] = 1
    return out


def score_binary_2d(a, b):
    h = len(a)
    w = len(a[0])
    n = float(h * w)
    sum_a = 0
    sum_b = 0
    inter = 0
    for y in range(h):
        ra = a[y]
        rb = b[y]
        for x in range(w):
            va = ra[x]
            vb = rb[x]
            if va: sum_a += 1
            if vb: sum_b += 1
            if va and vb: inter += 1
    if sum_a == 0 or sum_b == 0:
        return 0.0
    dice = (2.0 * inter) / (sum_a + sum_b + 1e-5)
    mean_a = sum_a / n
    mean_b = sum_b / n
    cov = inter - n * mean_a * mean_b
    var_a = sum_a * (1.0 - mean_a)
    var_b = sum_b * (1.0 - mean_b)
    denom = math.sqrt(max(0.0, var_a * var_b)) + 1e-5
    ncc = cov / denom
    return 0.55 * ncc + 0.45 * dice


def build_color_masks_pure(rgb_rows):
    h = len(rgb_rows)
    w = len(rgb_rows[0]) if h else 0
    masks = {name: zeros_2d(h, w) for name, _, _ in PALETTE}

    for y in range(h):
        row = rgb_rows[y]
        for x in range(w):
            r, g, b = row[x]
            max_c = r if (r >= g and r >= b) else (g if g >= b else b)
            min_c = r if (r <= g and r <= b) else (g if g <= b else b)
            sat = max_c - min_c
            lum = (r + g + b) / 3.0

            if lum > 195.0 and sat < 65.0:
                masks["W"][y][x] = 1
                continue
            if lum < 55.0 and sat < 75.0:
                masks["K"][y][x] = 1
                continue
            if sat <= 48.0:
                continue

            best_name = None
            best_d_sq = 1e9
            for name, pure_rgb, real_rgb in PALETTE:
                d1 = (r - pure_rgb[0]) ** 2 + (g - pure_rgb[1]) ** 2 + (b - pure_rgb[2]) ** 2
                d2 = (r - real_rgb[0]) ** 2 + (g - real_rgb[1]) ** 2 + (b - real_rgb[2]) ** 2
                d_sq = d1 if d1 < d2 else d2
                if d_sq < best_d_sq:
                    best_d_sq = d_sq
                    best_name = name
            if best_name not in ("W", "K") and best_d_sq < (115.0 ** 2):
                masks[best_name][y][x] = 1

    return masks


def remove_horizontal_lines_pure(rgb_rows, window=51):
    """
    Bộ lọc trung vị trượt ngang (window=51px) thuần Python:
    Tách toàn bộ các đường gạch ngang che mờ khỏi chữ cái ở dải trên.
    """
    h = len(rgb_rows)
    w = len(rgb_rows[0]) if h else 0
    pad = window // 2
    fg_loc = zeros_2d(h, w)

    for y in range(h):
        row = rgb_rows[y]
        out_r = fg_loc[y]
        # Tính nhanh bằng cách lấy mẫu bước 2px trong cửa sổ 51px (25 điểm)
        for x in range(24, min(235, w)):
            rs = []
            gs = []
            bs = []
            for dx in range(-pad, pad + 1, 2):
                xx = 0 if x + dx < 0 else (w - 1 if x + dx >= w else x + dx)
                pr, pg, pb = row[xx]
                rs.append(pr)
                gs.append(pg)
                bs.append(pb)
            rs.sort()
            gs.sort()
            bs.sort()
            mid = len(rs) // 2
            mr, mg, mb = rs[mid], gs[mid], bs[mid]
            r, g, b = row[x]
            dist_sq = (r - mr) ** 2 + (g - mg) ** 2 + (b - mb) ** 2
            if dist_sq > (40.0 ** 2):
                out_r[x] = 1
    return fg_loc


class CaptchaSolver:
    def __init__(self, samples_path=None):
        self.digit_bank = {}
        for d, rows in BUILTIN_DIGIT_BITMAPS.items():
            mat = [[1 if ch == "#" else 0 for ch in r[:12]] for r in rows[:16]]
            self.digit_bank[d] = [mat]
        one_nb = [list(r) for r in self.digit_bank["1"][0]]
        for r in range(12, 16):
            one_nb[r] = list(one_nb[6])
        self.digit_bank["1"].append(one_nb)

        raw_json = zlib.decompress(base64.b64decode(PACKED_SYMBOL_TEMPLATES_B64)).decode("utf-8")
        unpacked = json.loads(raw_json)
        self.upright_sym_bank = {
            ch: [unpack_16x16(t) for t in t_list] for ch, t_list in unpacked["u"].items()
        }
        self.rotated_sym_bank = {
            ch: [unpack_16x16(t) for t in t_list] for ch, t_list in unpacked["r"].items()
        }
        self.arrow_tmpl = [[1 if c == "#" else 0 for c in r] for r in ARROW_HEAD_ROWS]

    def score_all_odd_digits(self, crop_mask):
        """Tính điểm khớp cho cả 5 chữ số lẻ ('1', '3', '5', '7', '9') trên 5 nút cam."""
        odd_digits = ("1", "3", "5", "7", "9")
        tb = tight_bbox(crop_mask)
        if tb is None:
            return {d: 0.0 for d in odd_digits}
        y0, y1, x0, x1 = tb
        sub = crop_2d(crop_mask, y0, y1, x0, x1)
        norm = resize_area_binary(sub, 12, 16, threshold=0.33)
        scores = {}
        for digit in odd_digits:
            best_s = -1.0
            for tmpl in self.digit_bank.get(digit, []):
                inter = 0
                union = 0
                for r in range(16):
                    for c in range(12):
                        va = norm[r][c]
                        vb = tmpl[r][c]
                        if va and vb: inter += 1
                        if va or vb: union += 1
                iou = inter / float(union + 1e-5)
                ncc = score_binary_2d(norm, tmpl)
                sc = 0.55 * iou + 0.45 * ncc
                if sc > best_s:
                    best_s = sc
            scores[digit] = best_s
        return scores

    def classify_legend_symbol(self, sym_crop):
        tb = tight_bbox(sym_crop)
        if tb is None:
            return "?", 0.0
        sym_crop = crop_2d(sym_crop, tb[0], tb[1], tb[2], tb[3])
        valid_r = [r for r, row in enumerate(sym_crop) if sum(row) > 2]
        if len(valid_r) >= 10:
            sym_crop = sym_crop[valid_r[0] : valid_r[-1] + 1]
        h = len(sym_crop)
        w = len(sym_crop[0]) if h else 0
        if w > 14 and h <= 17 and sum(sum(row[14:]) for row in sym_crop[:5]) == 0:
            sym_crop = [row[:14] for row in sym_crop]
        elif w > 15:
            top_r = sum(sum(row[15:]) for row in sym_crop[:4])
            bot_r = sum(sum(row[15:]) for row in sym_crop[-4:])
            if top_r == 0 and bot_r == 0:
                sym_crop = [row[:15] for row in sym_crop]
        if h >= 17 and w > 10:
            for x_cut in range(5, min(15, w)):
                top_l = sum(sum(row[:x_cut]) for row in sym_crop[:5])
                bot_l = sum(sum(row[:x_cut]) for row in sym_crop[-5:])
                top_r = sum(sum(row[x_cut:]) for row in sym_crop[:5])
                bot_r = sum(sum(row[x_cut:]) for row in sym_crop[-5:])
                if top_l >= 4 and bot_l >= 4 and top_r == 0 and bot_r == 0:
                    sym_crop = [row[:x_cut] for row in sym_crop]
                    break
        if len(sym_crop) >= 12 and len(sym_crop[0]) >= 19:
            while len(sym_crop[0]) > 16 and sum(sym_crop[r][0] for r in range(len(sym_crop))) <= 6 and sum(sym_crop[r][0] for r in range(8)) == 0:
                sym_crop = [r[1:] for r in sym_crop]
            while len(sym_crop[0]) > 16:
                h_c = len(sym_crop)
                c_sum = sum(sym_crop[r][-1] for r in range(h_c))
                top8 = sum(sym_crop[r][-1] for r in range(8))
                bot_rest = sum(sym_crop[r][-1] for r in range(3, h_c))
                if (c_sum <= 4 and top8 == 0) or bot_rest == 0:
                    sym_crop = [r[:-1] for r in sym_crop]
                else:
                    break
        tb2 = tight_bbox(sym_crop)
        if tb2 is not None:
            sym_crop = crop_2d(sym_crop, tb2[0], tb2[1], tb2[2], tb2[3])
        h = len(sym_crop)
        w = len(sym_crop[0]) if h else 0

        if w <= 6 and h >= 14:
            return "L", 0.92

        norm = normalize_symbol_16(sym_crop)
        if w >= 19:
            pool = ["@", "%", "W", "M", "w", "m", "&"]
        elif h <= 16:
            pool = [c for c in XHEIGHT_LOWER if c not in ("m", "w")] + ["#", "$"]
        else:
            pool = [c for c in TALL_CHARS if c not in ("M", "W", "@", "%")]

        if h <= 16 and 12 <= w <= 16:
            bot_rows = sym_crop[-5:]
            col_fill = [sum(bot_rows[r][c] for r in range(len(bot_rows))) / float(len(bot_rows)) for c in range(w)]
            mid_slice = col_fill[w // 3 : max(w // 3 + 1, (2 * w) // 3)]
            mid_min = min(mid_slice) if mid_slice else 1.0
            left_leg = max(col_fill[: w // 3]) if w // 3 > 0 else 0.0
            right_leg = max(col_fill[(2 * w) // 3 :]) if (2 * w) // 3 < w else 0.0
            if left_leg > 0.80 and right_leg > 0.80 and mid_min < 0.25:
                pool = [c for c in pool if c in ("n", "u", "h", "r", "v", "x")]

        bot_right_empty = sum(sum(norm[r][11:15]) for r in range(11, 15)) == 0
        mid_left = sum(sum(norm[r][1:5]) for r in range(5, 9)) / 16.0
        mid_right = sum(sum(norm[r][9:13]) for r in range(5, 9)) / 16.0
        belly_left = sum(sum(norm[r][1:5]) for r in range(10, 14)) / 16.0
        bot_center = sum(sum(norm[r][5:10]) for r in range(13, 15)) / 10.0
        top_center = sum(sum(norm[r][5:11]) for r in range(0, 4)) / 24.0
        best_ch, best_s = "?", -1.0
        for ch in pool:
            for tmpl in self.upright_sym_bank.get(ch, []):
                s = score_binary_2d(norm, tmpl)
                if ch == "@" and bot_right_empty:
                    s += 0.15
                if ch.lower() == "a" and mid_left < 0.20 and belly_left < 0.20:
                    s -= 0.25
                if ch.lower() == "s":
                    if mid_left < 0.20 and mid_right > 0.60 and belly_left < 0.25:
                        s += 0.10
                    elif belly_left >= 0.45 and mid_right >= 0.40:
                        s -= 0.12
                if ch == "Q" and h >= 20 and not bot_right_empty and mid_right >= 0.35:
                    s += 0.12
                if ch.lower() == "c" and mid_right < 0.15 and mid_left >= 0.50:
                    s += 0.12
                if ch == "&" and belly_left >= 0.45 and mid_right >= 0.40:
                    s += 0.10
                if ch.lower() == "b":
                    if top_center < 0.25 and bot_center >= 0.50:
                        s -= 0.15
                    elif bot_center >= 0.60:
                        s += 0.08
                if ch.lower() == "u" and top_center < 0.25 and bot_center >= 0.50:
                    s += 0.12
                if s > best_s:
                    best_s = s
                    best_ch = ch
        return best_ch.upper(), round(best_s, 3)

    def extract_legend_entries(self, rgb_rows, H, W):
        y0_bot = int(round(H * 135.0 / 256.0))
        y1_bot = int(round(H * 230.0 / 256.0))
        bot_rows = rgb_rows[y0_bot:y1_bot]

        raw_masks = build_color_masks_pure(bot_rows)
        open_masks = {name: morph_open(m, 1, 3) for name, m in raw_masks.items()}
        close_masks = {name: morph_close(open_masks[name], 2, 6) for name in raw_masks}

        cells = [
            ("L1",  5, 33,  16, min(96, W)),
            ("L2", 32, 60,  16, min(96, W)),
            ("L3", 58, 88,  16, min(96, W)),
            ("R1",  5, 33, 146, min(244, W)),
            ("R2", 32, 60, 146, min(244, W)),
        ]

        used_colors = set()
        entries = {}
        for cname, cy0, cy1, cx0, cx1 in cells:
            best_color = None
            best_cnt = 0
            for name in ORDER:
                if name in used_colors:
                    continue
                sub = crop_2d(open_masks[name], cy0, cy1, cx0, cx1)
                cnt = sum(sum(r) for r in sub)
                if cnt > best_cnt:
                    best_cnt = cnt
                    best_color = name

            if best_color is None or best_cnt < 80:
                continue
            used_colors.add(best_color)

            cell_open = crop_2d(open_masks[best_color], cy0, cy1, cx0, cx1)
            cell_close = crop_2d(close_masks[best_color], cy0, cy1, cx0, cx1)

            for lx, ly, lw, lh, larea, _, pix in connected_components(cell_open):
                if larea < 12 or (lw <= 2 and larea < 18) or (lx == 0 and lw >= 12 and lh <= 9):
                    for py, px in pix:
                        cell_open[py][px] = 0

            sym_x0 = 0
            for x in range(len(cell_open[0])):
                if sum(cell_open[y][x] for y in range(len(cell_open))) >= 2:
                    sym_x0 = x
                    break

            dig_x0 = min(len(cell_close[0]) - 8, sym_x0 + 35)
            right_half = crop_2d(cell_close, 0, len(cell_close), dig_x0, len(cell_close[0]))
            d_comps = [c for c in connected_components(right_half) if c[4] >= 25 and c[3] >= 9 and c[2] >= 4]
            d_comps.sort(key=lambda c: c[0] + c[2], reverse=True)
            if d_comps:
                dx, dy, dw, dh, _, _, _ = d_comps[0]
                dig_crop = crop_2d(right_half, dy, dy + dh, dx, dx + dw)
            else:
                dig_crop = right_half
            dh_c = len(dig_crop)
            dw_c = len(dig_crop[0]) if dh_c else 0
            if dw_c > 16:
                right_open = crop_2d(cell_open, 0, len(cell_open), dig_x0, len(cell_open[0]))
                dig_open = crop_2d(right_open, dy, dy + dh, dx, dx + dw) if d_comps else right_open
                col_s = [sum(dig_crop[r][c] for r in range(dh_c)) for c in range(dw_c)]
                best_wx = max(range(0, dw_c - 13), key=lambda wx: sum(col_s[c] if col_s[c] >= 8 else 0 for c in range(wx, wx + 14)))
                dig_crop = [row[best_wx : best_wx + 14] for row in dig_open]
                for c in range(len(dig_crop[0])):
                    if sum(dig_crop[r][c] for r in range(dh_c)) <= 4:
                        for r in range(dh_c): dig_crop[r][c] = 0
                tb_d = tight_bbox(dig_crop)
                if tb_d is not None:
                    dig_crop = crop_2d(dig_crop, tb_d[0], tb_d[1], tb_d[2], tb_d[3])
            d_scores = self.score_all_odd_digits(dig_crop)
            if dw_c >= 40:
                d_scores["5"] = d_scores.get("5", 0.0) + 0.06

            sym_part_open = crop_2d(cell_open, 0, len(cell_open), sym_x0, min(len(cell_open[0]), sym_x0 + 24))
            sp_comps = connected_components(sym_part_open)
            has_narrow_stem = any(c[0] <= 3 and c[2] <= 5 and c[3] >= 15 for c in sp_comps)
            for lx, ly, lw, lh, larea, _, pix in sp_comps:
                if (lx >= 13 and lh <= 8) or (has_narrow_stem and lx >= 5 and lh <= 6):
                    for py, px in pix:
                        sym_part_open[py][px] = 0
            s_comps = [c for c in connected_components(sym_part_open) if c[4] >= 15]
            max_h = max((c[3] for c in s_comps), default=0)
            sym_part = morph_close(sym_part_open, 1, 4) if max_h < 14 else sym_part_open

            sym_char, sym_score = self.classify_legend_symbol(sym_part)
            entries[best_color] = {
                "cell": cname,
                "symbol": sym_char,
                "digit": "1",
                "sym_score": sym_score,
                "dig_score": 0.0,
                "all_dig_scores": d_scores,
            }

        colors_found = list(entries.keys())
        odd_digits = ("1", "3", "5", "7", "9")
        if 1 <= len(colors_found) <= 5:
            best_perm = max(
                itertools.permutations(odd_digits, len(colors_found)),
                key=lambda p: sum(entries[colors_found[i]]["all_dig_scores"].get(p[i], -1.0) for i in range(len(colors_found))),
            )
            for i, c_name in enumerate(colors_found):
                chosen_d = best_perm[i]
                entries[c_name]["digit"] = chosen_d
                entries[c_name]["dig_score"] = round(entries[c_name]["all_dig_scores"].get(chosen_d, 0.0), 3)
            for c_name in colors_found:
                entries[c_name].pop("all_dig_scores", None)

        return entries

    def classify_top_glyph(self, sub_raw, allowed_symbols, sub_loc=None):
        b_raw = morph_close(sub_raw, 2, 5)
        sub_clean = [row[:] for row in sub_raw]
        if len(sub_clean) > 0 and len(sub_clean[0]) >= 34:
            w_sc = len(sub_clean[0])
            for r_idx in range(len(sub_clean)):
                if sum(sub_clean[r_idx]) >= int(0.92 * w_sc):
                    sub_clean[r_idx] = [0] * w_sc
        opened = morph_open(sub_clean, 1, 3)
        b_open = morph_close(opened, 2, 6)
        b_loc = morph_close(sub_loc if sub_loc is not None else opened, 2, 6)

        norm_raw = normalize_symbol_16(b_raw)
        norm_open = normalize_symbol_16(b_open)
        norm_loc = normalize_symbol_16(b_loc)

        mid_left = sum(sum(norm_open[r][1:6]) for r in range(5, 12)) / float(7 * 5)
        mid_right = sum(sum(norm_open[r][10:15]) for r in range(5, 12)) / float(7 * 5)
        # '@' có vòng xoắn chữ 'a' ở giữa nhưng bị rỗng ở vùng giữa-trái (r=4..7, c=1..5) khi mở dọc
        upper_mid_left_open = sum(sum(norm_open[r][1:6]) for r in range(4, 7)) / 15.0
        center_raw = sum(sum(norm_raw[r][5:11]) for r in range(6, 11)) / 30.0

        best_sym = allowed_symbols[0] if allowed_symbols else "?"
        best_score = -1.0

        for sym_key in allowed_symbols:
            variants = [sym_key, sym_key.lower()] if sym_key.isalpha() else [sym_key]
            sym_score = -1.0
            for v in variants:
                for tmpl in self.rotated_sym_bank.get(v, []):
                    s_raw = score_binary_2d(norm_raw, tmpl)
                    s_open = score_binary_2d(norm_open, tmpl)
                    if sym_key in ("@", "%", "$"):
                        s = max(s_raw, 0.55 * s_open + 0.45 * s_raw)
                    else:
                        s = (0.65 * s_open + 0.35 * s_raw) if mid_left > 0.15 else s_raw
                    if s > sym_score:
                        sym_score = s

            top_arch = sum(sum(norm_open[r][4:12]) for r in range(1, 4)) / 24.0
            bot_arch = sum(sum(norm_open[r][4:12]) for r in range(11, 15)) / 32.0
            inner_hole = sum(sum(norm_open[r][6:10]) for r in range(5, 10)) / 20.0

            if sym_key in ("N", "M", "H", "U") and (mid_left < 0.35 or mid_right < 0.30):
                sym_score -= 0.18
            mid_right_raw = sum(sum(norm_raw[r][9:15]) for r in range(4, 11)) / 42.0

            if top_arch > 0.50 and bot_arch > 0.50 and inner_hole < 0.25:
                if sym_key in ("N", "M", "W", "Z", "X", "V", "K", "Y"):
                    sym_score -= 0.22
                if mid_right > 0.25 and sym_key in ("D", "O", "B", "Q", "0"):
                    sym_score += 0.10
                elif mid_right < 0.18 and sym_key == "C":
                    sym_score += 0.12
            if sym_key == "C":
                if mid_right_raw > 0.25 or mid_right > 0.25:
                    sym_score -= 0.25
                elif mid_right_raw < 0.12:
                    sym_score += 0.15
            top_arch_raw = sum(sum(norm_raw[r][5:10]) for r in range(1, 4)) / 15.0
            bot_arch_raw = sum(sum(norm_raw[r][5:10]) for r in range(12, 15)) / 15.0
            if sym_key == "%" and top_arch_raw > 0.50 and bot_arch_raw > 0.50:
                sym_score -= 0.20
            if sym_key == "B":
                if mid_right_raw < 0.18 or (top_arch_raw < 0.25 and bot_arch_raw < 0.25):
                    sym_score -= 0.25
                elif mid_right_raw > 0.35 and center_raw > 0.35 and top_arch_raw > 0.40 and bot_arch_raw > 0.40:
                    sym_score += 0.12
            if sym_key == "Z" and mid_left > 0.32:
                sym_score -= 0.12
            if sym_key == "@" and upper_mid_left_open < 0.25 and center_raw > 0.35 and len(sub_raw[0]) >= 28:
                sym_score += 0.22
            if sym_key == "U" and center_raw > 0.30:
                sym_score -= 0.25
            top_l_loc = sum(sum(norm_loc[r][0:4]) for r in range(1, 5))
            top_c_loc = sum(sum(norm_loc[r][5:11]) for r in range(1, 5)) / 24.0
            top_r_loc = sum(sum(norm_loc[r][12:16]) for r in range(1, 5))
            if top_l_loc == 0 and top_r_loc == 0 and top_c_loc >= 0.35:
                if sym_key == "T":
                    sym_score += 0.12
                elif sym_key in ("W", "M", "U", "L"):
                    sym_score -= 0.15
            if sym_key == "L" and len(sub_raw[0]) >= 22 and sum(sum(norm_loc[r][10:15]) for r in range(6, 10)) >= 4:
                sym_score -= 0.20
            if sym_key == "E" and mid_right > 0.30:
                sym_score -= 0.22
            if inner_hole > 0.55:
                if mid_left < 0.30 and mid_right < 0.30:
                    if sym_key == "X":
                        sym_score += 0.18
                    elif sym_key in ("Q", "O", "D", "C", "G", "U"):
                        sym_score -= 0.20
                elif sym_key == "&" and (mid_left >= 0.35 or mid_right >= 0.35):
                    sym_score += 0.22

            if sym_score > best_score:
                best_score = sym_score
                best_sym = sym_key

        def _count_runs(row):
            in_r = False
            runs = 0
            for v in row:
                if v and not in_r: runs += 1; in_r = True
                elif not v: in_r = False
            return runs

        runs_t = max(_count_runs(norm_open[1]), _count_runs(norm_open[2]))
        runs_b = max(_count_runs(norm_open[13]), _count_runs(norm_open[14]))
        center_f = sum(sum(norm_open[r][7:9]) for r in range(5, 9))
        wings = (sum(norm_open[6][0:3]) > 0 or sum(norm_open[7][0:3]) > 0) and (sum(norm_open[6][13:16]) > 0 or sum(norm_open[7][13:16]) > 0)
        is_hash = (runs_t >= 2 and runs_b >= 2 and center_f >= 2 and wings)

        bot_r_corner = sum(sum(norm_open[r][11:15]) for r in range(13, 16))
        loop_fill = sum(sum(norm_open[r][9:14]) for r in range(4, 9))

        if "#" in allowed_symbols and is_hash:
            best_sym = "#"
            best_score = 0.88
        elif "P" in allowed_symbols and bot_r_corner == 0 and loop_fill > 8 and best_sym in ("S",):
            best_sym = "P"
            best_score = 0.78

        return best_sym, round(float(best_score), 3)

    def extract_top_items(self, rgb_rows, H, W, legend_entries, target_len=TARGET_LEN):
        y_top = min(66, int(H * 0.27))
        top_rows = rgb_rows[0:y_top]

        fg_loc = remove_horizontal_lines_pure(top_rows, window=51)
        raw_masks = build_color_masks_pure(top_rows)
        allowed_symbols = [
            info["symbol"] for info in legend_entries.values() if info.get("symbol") and info["symbol"] != "?"
        ]

        items = []

        # Quét TOÀN BỘ 7 MÀU trong PALETTE (vì chữ trên Top Strip có thể mang màu thứ 6 không nằm trong 5 màu Legend!)
        for color_name in ORDER:
            raw_m = raw_masks[color_name]
            loc_m = zeros_2d(y_top, W)
            for y in range(y_top):
                for x in range(24, min(235, W)):
                    if raw_m[y][x] and fg_loc[y][x]:
                        loc_m[y][x] = 1

            loc_u8 = morph_close(morph_open(loc_m, 1, 2), 5, 7)
            comps = connected_components(loc_u8)
            clusters = []
            for x, y, w, h, area, x_mean, _ in comps:
                if area >= 15 and h >= 4 and w >= 4:
                    clusters.append((x_mean, float(area), x, y, w, h))

            clusters.sort(key=lambda t: t[0])
            merged = []
            for cl in clusters:
                if not merged:
                    merged.append(cl)
                else:
                    px_m, p_a, px, py, pw, ph = merged[-1]
                    cx_m, c_a, cx, cy, cw, ch = cl
                    if abs(cx_m - px_m) < 25.0 or cx <= px + pw + 4:
                        tot_a = p_a + c_a
                        nx_m = (px_m * p_a + cx_m * c_a) / tot_a
                        nx0, ny0 = min(px, cx), min(py, cy)
                        nx1, ny1 = max(px + pw, cx + cw), max(py + ph, cy + ch)
                        merged[-1] = (nx_m, tot_a, nx0, ny0, nx1 - nx0, ny1 - ny0)
                    else:
                        merged.append(cl)

            # Lọc bỏ các mảnh đường kẻ nhiễu ngang còn sót (chữ thật luôn có chiều cao h >= 15 và diện tích >= 75)
            valid_merged = [m for m in merged if m[5] >= 14 and m[1] >= 40]
            if not valid_merged:
                continue

            # Nếu có hơn 1 cụm cùng màu, chỉ giữ cụm thứ 2 nếu thực sự là chữ thứ 2 (area >= 130 và h >= 18)
            valid_merged.sort(key=lambda m: m[1], reverse=True)
            kept = [valid_merged[0]]
            for extra in valid_merged[1:]:
                if extra[1] >= 130 and extra[5] >= 18:
                    kept.append(extra)
            kept.sort(key=lambda m: m[0])

            for x_mean, area, x, y, w, h in kept:

                in_xs = []
                in_ys = []
                for iy in range(y_top):
                    for ix in range(max(24, int(x_mean - 17)), min(W - 18, int(x_mean + 18))):
                        if loc_u8[iy][ix]:
                            in_xs.append(ix)
                            in_ys.append(iy)
                if len(in_xs) >= 10:
                    x0, x1 = max(24, min(in_xs)), min(W - 18, max(in_xs) + 1)
                    y0, y1 = max(0, min(in_ys)), min(y_top, max(in_ys) + 1)
                else:
                    x0, x1 = max(24, x), min(W - 18, x + w)
                    y0, y1 = max(0, y), min(y_top, y + h)

                sub_raw = crop_2d(raw_m, y0, y1, x0, x1)
                sub_loc = crop_2d(loc_m, y0, y1, x0, x1)
                sym_pred, sym_sc = self.classify_top_glyph(sub_raw, allowed_symbols, sub_loc=sub_loc)
                items.append({
                    "x": round(float(x_mean), 1),
                    "color": color_name,
                    "symbol": sym_pred,
                    "sym_score": sym_sc,
                    "area": float(area),
                    "w": int(x1 - x0),
                    "h": int(y1 - y0),
                })

        items.sort(key=lambda item: item["x"])

        if not target_len or target_len <= 0:
            if len(items) > 6:
                items = sorted(items, key=lambda item: item["area"], reverse=True)[:6]
                items.sort(key=lambda item: item["x"])
            return items

        if len(items) > target_len:
            items = sorted(items, key=lambda item: item["area"], reverse=True)[:target_len]
            items.sort(key=lambda item: item["x"])
        while 0 < len(items) < target_len:
            counts = {}
            for it in items:
                counts[it["color"]] = counts.get(it["color"], 0) + 1
            best_idx = 0
            best_w = -1.0
            for idx, it in enumerate(items):
                pen = 0.35 if counts.get(it["color"], 0) >= 2 else 1.0
                weight = (it["area"] + 0.18 * (it["w"] * it["h"])) * pen
                if weight > best_w:
                    best_w = weight
                    best_idx = idx
            dup = dict(items[best_idx])
            items[best_idx]["x"] = round(dup["x"] - 1.5, 1)
            items[best_idx]["area"] *= 0.5
            dup["x"] = round(dup["x"] + 1.5, 1)
            dup["area"] *= 0.5
            items.insert(best_idx + 1, dup)
            items.sort(key=lambda item: item["x"])

        return items

    def solve_image(self, image_path, target_len=TARGET_LEN):
        try:
            H, W, rgb_rows = decode_png_pure(image_path)
        except Exception as exc:
            return None, {"error": f"Cannot decode PNG: {exc}"}

        legend_entries = self.extract_legend_entries(rgb_rows, H, W)
        if not legend_entries:
            return None, {"error": "No legend entries detected"}

        symbol_to_digit = {}
        color_to_digit = {}
        for color_name, info in legend_entries.items():
            color_to_digit[color_name] = info["digit"]
            if info["symbol"] and info["symbol"] != "?":
                symbol_to_digit[info["symbol"].upper()] = info["digit"]

        top_items = self.extract_top_items(rgb_rows, H, W, legend_entries, target_len=target_len)

        digits_by_symbol = []
        digits_by_color = []
        final_digits = []
        mode = os.environ.get("CAPTCHA_MODE", "symbol").lower()

        for it in top_items:
            c_dig = color_to_digit.get(it["color"], "1")
            s_dig = symbol_to_digit.get(it["symbol"], c_dig)
            digits_by_color.append(c_dig)
            digits_by_symbol.append(s_dig)

            if mode == "color":
                final_digits.append(c_dig)
            else:
                if it["symbol"] in symbol_to_digit:
                    final_digits.append(s_dig)
                else:
                    final_digits.append(c_dig)

        answer = "".join(final_digits)
        button_digits = sorted(set(color_to_digit.values()))

        fallback_answer = "".join(digits_by_color) if "".join(digits_by_color) != answer else answer
        details = {
            "mode": mode,
            "detected_length": len(answer),
            "legend_symbol_map": symbol_to_digit,
            "legend_color_map": color_to_digit,
            "button_digits": button_digits,
            "top_detected": [
                {"x": it["x"], "char": it["symbol"], "color": it["color"], "score": it["sym_score"]}
                for it in top_items
            ],
            "answer_by_symbol": "".join(digits_by_symbol),
            "answer_by_color": "".join(digits_by_color),
            "fallback_answer": fallback_answer,
            "answer": answer,
        }
        return answer, details


# ==============================================================================
# TỰ ĐỘNG CẤU HÌNH HỆ THỐNG & CLICK 5 NÚT CAM VÀO CỬA SỔ GAME
# ==============================================================================
def auto_elevate_admin():
    if os.name != "nt" or os.environ.get("CAPTCHA_NO_ELEVATE") == "1":
        return
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("[AUTO-SETUP] Dang nang quyen Administrator de tu dong bam phim/chuot vao game...")
            params = " ".join([f'"{arg}"' for arg in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit(0)
    except Exception:
        pass


def auto_configure_all_mod_folders():
    current_file = Path(__file__).resolve()
    py_exe = sys.executable

    for root in MOD_ROOTS:
        if not root.exists():
            continue

        cfg_path = root / "BepInEx" / "config" / "NroPort.Plugin.cfg"
        if cfg_path.is_file():
            try:
                content = cfg_path.read_text(encoding="utf-8", errors="ignore")
                new_content = re.sub(r"(?m)^(\s*Bat\s*=\s*).*$", r"\g<1>true", content)
                new_content = re.sub(r"(?m)^(\s*TuDongGui\s*=\s*).*$", r"\g<1>true", new_content)
                new_content = re.sub(r"(?m)^(\s*ChanBat\s*=\s*).*$", r"\g<1>false", new_content)
                if new_content != content:
                    cfg_path.write_text(new_content, encoding="utf-8")
                    print(f"[AUTO-SETUP] Da tu dong sua cau hinh: {cfg_path}")
                else:
                    print(f"[AUTO-SETUP] Cau hinh da chuan: {cfg_path}")
            except Exception as exc:
                print(f"[AUTO-SETUP] Loi khi sua {cfg_path}: {exc}")

        cap_dir = root / "tudzday-captcha"
        cap_dir.mkdir(parents=True, exist_ok=True)
        target_py = cap_dir / "solve_legend.py"
        try:
            if current_file != target_py:
                shutil.copy2(current_file, target_py)
                print(f"[AUTO-SETUP] Da dong bo file solver vao: {target_py}")
        except Exception:
            pass

        bat_path = root / "Bat-Auto-Captcha.bat"
        bat_content = (
            "@echo off\r\n"
            "title AUTO CAPTCHA NRO (5 SO & 6 SO) - DANG CHAY\r\n"
            "echo ============================================================\r\n"
            "echo   DANG KHOI DONG AUTO GIAI + TU DONG NHAP CAPTCHA (5 & 6 SO)\r\n"
            "echo ============================================================\r\n"
            "taskkill /F /IM pythonw.exe 2>nul\r\n"
            f'"{py_exe}" "{target_py}"\r\n'
            "pause\r\n"
        )
        try:
            bat_path.write_text(bat_content, encoding="utf-8")
            print(f"[AUTO-SETUP] Da tao nut bat 1 cham: {bat_path}")
        except Exception:
            pass


def find_game_hwnd(target_pid=None):
    if os.name != "nt":
        return None
    user32 = ctypes.windll.user32
    found_hwnds = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        cw = rect.right - rect.left
        ch = rect.bottom - rect.top
        if cw < 300 or ch < 200:
            return True
        if target_pid and pid.value == target_pid:
            found_hwnds.insert(0, (hwnd, cw * ch))
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()
            if any(k in title for k in ("nro", "ngoc rong", "dragon", "mod", "boy", "tudzday")):
                found_hwnds.append((hwnd, cw * ch))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return found_hwnds[0][0] if found_hwnds else None


def auto_input_to_game_window(answer, button_digits, target_pid=None):
    if os.name != "nt" or not AUTO_INPUT_GAME or not answer:
        return "skipped"
    try:
        user32 = ctypes.windll.user32
        hwnd = find_game_hwnd(target_pid)

        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_CHAR = 0x0102
        MK_LBUTTON = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        VK_RETURN = 0x0D

        if len(button_digits) != 5:
            button_digits = ["1", "3", "5", "7", "9"]
        digit_to_btn_idx = {d: idx for idx, d in enumerate(button_digits)}

        client_w, client_h = 1024, 528
        pt_origin = wintypes.POINT(0, 0)

        if hwnd:
            try:
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)
                # Mở khoá SetForegroundWindow của Windows bằng phím ALT (0x12)
                user32.keybd_event(0x12, 0, 0, 0)
                user32.SetForegroundWindow(hwnd)
                user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
            except Exception:
                pass
            rect = wintypes.RECT()
            if user32.GetClientRect(hwnd, ctypes.byref(rect)):
                cw = rect.right - rect.left
                ch = rect.bottom - rect.top
                if cw > 200 and ch > 150:
                    client_w, client_h = cw, ch
            user32.ClientToScreen(hwnd, ctypes.byref(pt_origin))

        old_cursor = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(old_cursor))

        for ch_dig in answer:
            if not ch_dig.isdigit():
                continue
            if AUTO_CLICK_ORANGE_BUTTONS and ch_dig in digit_to_btn_idx:
                btn_idx = digit_to_btn_idx[ch_dig]
                rel_x = int(round(client_w * ORANGE_BTN_X_PCTS[btn_idx]))
                rel_y = int(round(client_h * ORANGE_BTN_Y_PCT))
                lparam = (rel_y << 16) | (rel_x & 0xFFFF)
                if hwnd:
                    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
                    time.sleep(0.015)
                    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)
                if hwnd:
                    user32.SetCursorPos(pt_origin.x + rel_x, pt_origin.y + rel_y)
                    time.sleep(0.01)
                    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(0.015)
                    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

            if AUTO_PRESS_NUMBER_KEYS:
                vk = ord(ch_dig)
                if hwnd:
                    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
                    user32.PostMessageW(hwnd, WM_CHAR, vk, 0)
                    time.sleep(0.01)
                    user32.PostMessageW(hwnd, WM_KEYUP, vk, 0)
                if not hwnd or user32.GetForegroundWindow() == hwnd:
                    user32.keybd_event(vk, 0, 0, 0)
                    time.sleep(0.01)
                    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

            time.sleep(STEP_DELAY_SEC)

        if AUTO_PRESS_NUMBER_KEYS:
            if hwnd:
                user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0)
                user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0)
            if not hwnd or user32.GetForegroundWindow() == hwnd:
                user32.keybd_event(VK_RETURN, 0, 0, 0)
                time.sleep(0.01)
                user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

        if AUTO_CLICK_ORANGE_BUTTONS and hwnd:
            user32.SetCursorPos(old_cursor.x, old_cursor.y)

        return f"ok(hwnd={hwnd},size={client_w}x{client_h})"
    except Exception as exc:
        return f"err({exc})"


def resolve_all_runtime_dirs(explicit_dir=None):
    dirs = []
    if explicit_dir:
        dirs.append(Path(explicit_dir))
    env_dir = os.environ.get("CAPTCHA_RUNTIME_DIR")
    if env_dir:
        dirs.append(Path(env_dir))

    script_dir = Path(__file__).resolve().parent
    candidates = [
        Path(r"C:\Users\Tuchuai\Downloads\Mod-250-PC\tudzday-captcha"),
        Path(r"C:\Users\Tuchuai\Desktop\Mod-250-PC\tudzday-captcha"),
        script_dir if script_dir.name == "tudzday-captcha" else script_dir / "tudzday-captcha",
        Path.cwd() if Path.cwd().name == "tudzday-captcha" else Path.cwd() / "tudzday-captcha",
    ]
    for c in candidates:
        if c.exists() and c not in dirs:
            dirs.append(c)
    if not dirs:
        dirs.append(Path(r"C:\Users\Tuchuai\Downloads\Mod-250-PC\tudzday-captcha"))
    return dirs


def append_log(log_path, message):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}\n"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(line, end="", flush=True)


def watch_loop(runtime_dirs, solver):
    for rdir in runtime_dirs:
        (rdir / "inbox").mkdir(parents=True, exist_ok=True)
        (rdir / "jobs").mkdir(parents=True, exist_ok=True)
        (rdir / "outbox").mkdir(parents=True, exist_ok=True)
        append_log(
            rdir / "solver.log",
            f"SAN SANG (100% Pure Python - Khong can numpy/cv2)! Dang theo doi tai: {[str(d) for d in runtime_dirs]}",
        )

    processed = set()
    # Bỏ qua các file ảnh CAPTCHA cũ tồn đọng trong inbox từ trước khi bật tool (cũ hơn 15 giây)
    now_ts = time.time()
    for rdir in runtime_dirs:
        for old_png in (rdir / "inbox").glob("*.png"):
            try:
                if (now_ts - old_png.stat().st_mtime) > 15.0:
                    processed.add(f"{rdir}:{old_png.stem}")
            except Exception:
                pass

    while True:
        try:
            for runtime_dir in runtime_dirs:
                inbox_dir = runtime_dir / "inbox"
                jobs_dir = runtime_dir / "jobs"
                outbox_dir = runtime_dir / "outbox"
                log_path = runtime_dir / "solver.log"

                for png_path in sorted(inbox_dir.glob("*.png"), key=lambda p: p.stat().st_mtime):
                    sha = png_path.stem
                    key_id = f"{runtime_dir}:{sha}"
                    out_path = outbox_dir / f"{sha}.txt"
                    if key_id in processed:
                        continue

                    target_len = TARGET_LEN
                    target_pid = None
                    job_path = jobs_dir / f"{sha}.json"
                    if job_path.exists():
                        try:
                            job_data = json.loads(job_path.read_text(encoding="utf-8"))
                            ans_len = int(job_data.get("answerLength", 0) or 0)
                            if ans_len >= 5:
                                target_len = ans_len
                            pid_val = int(job_data.get("pid", 0) or 0)
                            if pid_val > 0:
                                target_pid = pid_val
                        except Exception:
                            pass

                    if png_path.stat().st_size < 100:
                        time.sleep(0.02)

                    t0 = time.perf_counter()
                    answer, details = solver.solve_image(png_path, target_len=target_len)
                    dt_ms = (time.perf_counter() - t0) * 1000.0

                    if answer:
                        tmp_path = outbox_dir / f"{sha}.tmp"
                        tmp_path.write_text(answer, encoding="utf-8")
                        tmp_path.replace(out_path)
                        processed.add(key_id)

                        btn_digits = details.get("button_digits", ["1", "3", "5", "7", "9"])
                        input_status = auto_input_to_game_window(answer, btn_digits, target_pid=target_pid)

                        chars_str = "".join(it["char"] for it in details.get("top_detected", []))
                        append_log(
                            log_path,
                            f"SOLVED ({len(answer)} so) {sha} -> {answer} ({dt_ms:.1f}ms) | input={input_status} "
                            f"| top_chars={chars_str} | sym_map={details.get('legend_symbol_map')} | by_color={details.get('answer_by_color')}",
                        )
                    else:
                        append_log(log_path, f"FAIL {sha} ({dt_ms:.1f}ms) | details={details}")
                        processed.add(key_id)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            for rdir in runtime_dirs:
                append_log(rdir / "solver.log", f"ERROR in loop: {exc}\n{traceback.format_exc()}")

        time.sleep(POLL_INTERVAL_SEC)


def main():
    img_arg = None
    if len(sys.argv) >= 3 and sys.argv[1] in ("--image", "-i"):
        img_arg = sys.argv[2]
    elif len(sys.argv) >= 2 and sys.argv[1].lower().endswith((".png", ".jpg", ".jpeg")):
        img_arg = sys.argv[1]
    if img_arg:
        test_img = Path(img_arg)
        solver = CaptchaSolver()
        t0 = time.perf_counter()
        ans, details = solver.solve_image(test_img, target_len=TARGET_LEN)
        dt = (time.perf_counter() - t0) * 1000.0
        print(json.dumps({"file": str(test_img), "time_ms": round(dt, 1), "answer": ans, "details": details}, ensure_ascii=False, indent=2))
        return

    auto_elevate_admin()
    auto_configure_all_mod_folders()

    solver = CaptchaSolver()
    runtime_dirs = resolve_all_runtime_dirs(sys.argv[1] if len(sys.argv) >= 2 else None)
    watch_loop(runtime_dirs, solver)


if __name__ == "__main__":
    main()
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from abc import ABC, abstractmethod

import requests


class CryptoAPI(ABC):

    def __init__(self, base_url):
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "CryptoRatesStudentProject/1.0"})

    def _get_json(self, endpoint, params=None):
        response = self._session.get(
            f"{self._base_url}/{endpoint.lstrip('/')}",
            params=params,
            timeout=12
        )
        if response.status_code == 429:
            raise Exception("Превышен лимит запросов к CoinGecko API. Подождите минуту.")
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def get_tickers(self):
        raise NotImplementedError


class CoinGeckoAPI(CryptoAPI):

    def __init__(self, api_key=None):
        super().__init__("https://api.coingecko.com/api/v3")
        if api_key:
            self._session.headers.update({"x-cg-demo-api-key": api_key})

    def get_tickers(self):
        raw = self._get_json("coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": "false"
        })
        rows = []
        for item in raw:
            rows.append({
                "id": item.get("id", ""),
                "name": item.get("name", "Unknown"),
                "symbol": item.get("symbol", "").upper(),
                "price": float(item.get("current_price") or 0),
                "change": float(item.get("price_change_percentage_24h") or 0),
                "rank": int(item.get("market_cap_rank") or 999999),
            })
        rows.sort(key=lambda x: x["rank"])
        return rows


class CryptoApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Курсы криптовалют (CoinGecko)")
        self.root.geometry("820x480")
        self.root.minsize(680, 400)

        self.api = CoinGeckoAPI()

        self._tickers = []
        self._busy = False
        self._auto_refresh = True

        self._build_ui()
        self.refresh_prices()
        self.root.after(60_000, self._auto_refresh_loop)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        heading = ttk.Label(outer, text="Курсы криптовалют", font=("Segoe UI", 18, "bold"))
        heading.pack(anchor="w", pady=(0, 8))

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(0, 8))

        ttk.Label(controls, text="Поиск по тикеру:").pack(side="left")
        self.search_var = tk.StringVar(value="")
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(controls, textvariable=self.search_var, width=16).pack(side="left", padx=(6, 14))

        self.refresh_button = ttk.Button(controls, text="Обновить", command=self.refresh_prices)
        self.refresh_button.pack(side="right")

        table_frame = ttk.LabelFrame(outer, text="Текущие котировки (USD)", padding=6)
        table_frame.pack(fill="both", expand=True)

        columns = ("rank", "symbol", "name", "price", "change")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.table.heading("rank", text="#")
        self.table.heading("symbol", text="Тикер")
        self.table.heading("name", text="Название")
        self.table.heading("price", text="Цена, USD")
        self.table.heading("change", text="Изменение за 24 ч.")
        self.table.column("rank", width=50, anchor="center")
        self.table.column("symbol", width=90, anchor="center")
        self.table.column("name", width=260)
        self.table.column("price", width=180, anchor="e")
        self.table.column("change", width=170, anchor="e")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.status_var = tk.StringVar(value="Подключение к API…")
        ttk.Label(outer, textvariable=self.status_var, anchor="w").pack(fill="x", pady=(8, 0))

    def refresh_prices(self):
        if self._busy:
            return
        self._busy = True
        self.refresh_button.configure(state="disabled")
        self.status_var.set("Загрузка котировок…")
        threading.Thread(target=self._load_prices_worker, daemon=True).start()

    def _load_prices_worker(self):
        try:
            tickers = self.api.get_tickers()
            self.root.after(0, lambda data=tickers: self._show_prices(data))
        except Exception as exc:
            self.root.after(0, lambda error=str(exc): self._show_error(error))

    def _show_prices(self, tickers):
        self._tickers = tickers
        self._apply_filter()
        self.status_var.set(
            f"Обновлено: {datetime.now().strftime('%H:%M:%S')} · Источник: CoinGecko · "
            f"Автообновление каждые 60 с"
        )
        self._busy = False
        self.refresh_button.configure(state="normal")

    def _apply_filter(self):
        query = self.search_var.get().strip().upper()
        for item in self.table.get_children():
            self.table.delete(item)

        for coin in self._tickers[:20]:
            if query and query not in coin["symbol"].upper() and query not in coin["name"].upper():
                continue
            self.table.insert(
                "", "end", iid=coin["id"],
                values=(
                    coin["rank"],
                    coin["symbol"],
                    coin["name"],
                    f'{coin["price"]:,.8f}'.rstrip("0").rstrip("."),
                    f'{coin["change"]:+.2f}%'
                )
            )

    def _show_error(self, error):
        self._busy = False
        self.refresh_button.configure(state="normal")
        self.status_var.set("Ошибка загрузки котировок. Проверьте подключение к интернету.")
        messagebox.showerror(
            "Ошибка API",
            "Не удалось получить котировки.\n"
            "Проверьте подключение к интернету и попробуйте ещё раз.\n\n"
            f"Подробности: {error}"
        )

    def _auto_refresh_loop(self):
        if self._auto_refresh:
            self.refresh_prices()
        self.root.after(60_000, self._auto_refresh_loop)


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    CryptoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
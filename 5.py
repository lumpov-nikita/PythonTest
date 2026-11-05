import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Еще коммит
def exchange():
    base1 = base1_var.get().upper()
    base2 = base2_var.get().upper()
    target = target_var.get().upper()

    url1 = f"https://open.er-api.com/v6/latest/{base1}"
    url2 = f"https://open.er-api.com/v6/latest/{base2}"

    try:
        response1 = requests.get(url1, timeout=5)
        response2 = requests.get(url2, timeout=5)

        data1 = response1.json()
        data2 = response2.json()

        if data1.get("result") == "success" and data2.get("result") == "success":
            rate1 = data1["rates"].get(target)
            rate2 = data2["rates"].get(target)

            if rate1 is not None and rate2 is not None:
                result_text = (
                    f"1 {base1} = {rate1:.4f} {target}\n"
                    f"1 {base2} = {rate2:.4f} {target}"
                )
                result_label.config(text=result_text)
            else:
                messagebox.showerror("Ошибка", "Не удалось найти курс для выбранной целевой валюты.")
        else:
            messagebox.showerror("Ошибка", "API вернул ошибку. Проверьте коды валют.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка сети", f"Не удалось выполнить запрос: {e}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

root = tk.Tk()
root.title("Курсы обмена валют")
root.geometry("300x450")

currencies = ["EUR", "USD", "RUB", "GBP", "JPY", "CNY", "CHF", "CAD"]

base1_var = tk.StringVar(value="EUR")
base2_var = tk.StringVar(value="USD")
target_var = tk.StringVar(value="RUB")

tk.Label(root, text="Базовая валюта 1").pack(pady=(10, 0))
ttk.Combobox(root, textvariable=base1_var, values=currencies, state="readonly").pack()

tk.Label(root, text="Базовая валюта 2").pack(pady=(10, 0))
ttk.Combobox(root, textvariable=base2_var, values=currencies, state="readonly").pack()

tk.Label(root, text="Целевая валюта").pack(pady=(10, 0))
ttk.Combobox(root, textvariable=target_var, values=currencies, state="readonly").pack()

tk.Button(root, text="Получить курс обмена", command=exchange).pack(pady=20)

result_label = tk.Label(root, text="", font=("Arial", 10))
result_label.pack()

root.mainloop()
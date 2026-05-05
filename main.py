import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GitHub User Finder")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.favorites = self.load_favorites()
        
        self.create_widgets()

    def create_widgets(self):
        # === Верхняя панель поиска ===
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Поиск пользователя GitHub:").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_users())

        ttk.Button(search_frame, text="🔍 Искать", command=self.search_users).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="❤️ Избранное", command=self.show_favorites).pack(side=tk.LEFT, padx=5)

        # === Результаты поиска ===
        result_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview для результатов
        columns = ("login", "name", "followers", "repos")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("login", text="Логин")
        self.tree.heading("name", text="Имя")
        self.tree.heading("followers", text="Подписчики")
        self.tree.heading("repos", text="Репозитории")
        
        self.tree.column("login", width=150)
        self.tree.column("name", width=200)
        self.tree.column("followers", width=100)
        self.tree.column("repos", width=100)
        
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_user_double_click)

        # === Статусбар ===
        self.status_var = tk.StringVar(value="Готов к поиску")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def search_users(self):
        query = self.search_var.get().strip()
        
        if not query:
            messagebox.showwarning("Ошибка", "Поле поиска не должно быть пустым!")
            return

        self.status_var.set(f"Поиск по запросу: {query}...")
        self.root.update()

        try:
            url = f"https://api.github.com/search/users?q={query}&per_page=20"
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            users = data.get("items", [])
            
            # Очистка предыдущих результатов
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if not users:
                self.status_var.set("Пользователи не найдены")
                return

            for user in users:
                # Получаем дополнительные данные
                try:
                    user_detail = requests.get(user['url'], headers=headers, timeout=5).json()
                    name = user_detail.get('name', '—')
                    followers = user_detail.get('followers', 0)
                    public_repos = user_detail.get('public_repos', 0)
                except:
                    name = '—'
                    followers = 0
                    public_repos = 0

                self.tree.insert("", tk.END, values=(
                    user['login'],
                    name,
                    followers,
                    public_repos
                ), tags=(user['login'],))

            self.status_var.set(f"Найдено пользователей: {len(users)}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка при запросе к GitHub API:\n{str(e)}")
            self.status_var.set("Ошибка запроса")

    def on_user_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        values = self.tree.item(selected[0])['values']
        login = values[0]
        
        if messagebox.askyesno("Добавить в избранное?", f"Добавить пользователя @{login} в избранное?"):
            self.add_to_favorites(login)

    def add_to_favorites(self, login):
        if login in [fav['login'] for fav in self.favorites]:
            messagebox.showinfo("Уже в избранном", f"@{login} уже находится в избранном")
            return

        try:
            user = requests.get(f"https://api.github.com/users/{login}").json()
            
            favorite = {
                "login": user['login'],
                "name": user.get('name', '—'),
                "avatar_url": user.get('avatar_url'),
                "html_url": user['html_url'],
                "followers": user.get('followers', 0),
                "public_repos": user.get('public_repos', 0),
                "added_at": datetime.now().isoformat()
            }
            
            self.favorites.append(favorite)
            self.save_favorites()
            messagebox.showinfo("Успешно", f"@{login} добавлен в избранное!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить пользователя:\n{str(e)}")

    def load_favorites(self):
        if os.path.exists("favorites.json"):
            try:
                with open("favorites.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_favorites(self):
        with open("favorites.json", "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)

    def show_favorites(self):
        if not self.favorites:
            messagebox.showinfo("Избранное", "Список избранного пуст")
            return

        fav_window = tk.Toplevel(self.root)
        fav_window.title("Избранные пользователи")
        fav_window.geometry("700x500")

        tree = ttk.Treeview(fav_window, columns=("login", "name", "followers"), show="headings")
        tree.heading("login", text="Логин")
        tree.heading("name", text="Имя")
        tree.heading("followers", text="Подписчики")
        
        for fav in self.favorites:
            tree.insert("", tk.END, values=(fav['login'], fav['name'], fav['followers']))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

---

### 3. `.gitignore`

```gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.DS_Store
favorites.json
.venv/
venv/

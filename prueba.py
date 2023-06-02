import tkinter as tk
from tkinter import filedialog
import re
from bs4 import BeautifulSoup
import networkx as nx
import matplotlib.pyplot as plt

class DOMViewer(tk.Toplevel):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title("DOM Mapa Mental")

        self.canvas = tk.Canvas(self)
        self.canvas.pack(side="left", fill="both", expand=True)

    def update_dom_tree(self, soup):
        G = self.create_dom_graph(soup)
        self.draw_dom_graph(G)

    def create_dom_graph(self, soup):
        G = nx.DiGraph()

        def add_node_and_edges(node):
            if node.name:
                G.add_node(node.name)
                for child in node.children:
                    if child.name:
                        G.add_edge(node.name, child.name)
                    add_node_and_edges(child)

        add_node_and_edges(soup)

        return G

    def draw_dom_graph(self, G):
        pos = nx.spring_layout(G, seed=42)  # Posicionamiento del grafo

        plt.figure(figsize=(8, 6))  # Tamaño de la figura
        nx.draw(G, pos, with_labels=True, node_size=2000, font_size=10, node_color="lightblue", edge_color="gray", width=1.0)  # Dibujar el grafo
        plt.axis("off")  # Ocultar los ejes

        plt.tight_layout()  # Ajustar el diseño de la figura
        plt.savefig("dom_graph.png")  # Guardar el gráfico como imagen
        plt.close()

        self.canvas.delete("all")  # Borrar contenido anterior del lienzo
        img = tk.PhotoImage(file="dom_graph.png")  # Cargar la imagen del gráfico
        self.canvas.create_image(0, 0, anchor="nw", image=img)  # Mostrar la imagen en el lienzo
        self.canvas.image = img  # Guardar una referencia para evitar que la imagen sea eliminada por el recolector de basura

class SyntaxHighlightText(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.linenumbers = tk.Text(self, width=4, padx=5, pady=5, takefocus=0, border=0, background="#f0f0f0", state="disabled")
        self.linenumbers.pack(side="left", fill="y")

        self.text_widget = tk.Text(self)
        self.text_widget.pack(side="right", fill="both", expand=True)

        self.text_widget.bind("<KeyRelease>", self.highlight_syntax)
        self.text_widget.bind("<Return>", self.update_linenumbers)
        self.text_widget.bind("<MouseWheel>", self.on_mousewheel)
        self.text_widget.bind("<Configure>", self.on_configure)

        self.tag_configure("open_tag", foreground="blue")
        self.tag_configure("close_tag", foreground="red")

        self.create_menu()

        self.dom_viewer = None

    def tag_configure(self, tag, **kwargs):
        self.text_widget.tag_configure(tag, **kwargs)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Abrir", command=self.open_file)
        file_menu.add_command(label="Guardar", command=self.save_file)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Actualizar", command=self.update_syntax_highlight)
        menubar.add_cascade(label="Editar", menu=edit_menu)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "r") as file:
                content = file.read()
                self.text_widget.delete("1.0", "end")
                self.text_widget.insert("1.0", content)
                self.update_linenumbers()

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            content = self.text_widget.get("1.0", "end")
            with open(file_path, "w") as file:
                file.write(content)

    def on_mousewheel(self, event):
        self.linenumbers.yview("scroll", -event.delta, "units")
        self.text_widget.yview("scroll", -event.delta, "units")

    def on_configure(self, event=None):
        self.linenumbers.configure(height=self.text_widget.winfo_height())
        self.update_linenumbers()

    def highlight_syntax(self, event):
        self.text_widget.tag_remove("open_tag", "1.0", "end")
        self.text_widget.tag_remove("close_tag", "1.0", "end")

        html_text = self.text_widget.get("1.0", "end")
        self.highlight_tags(html_text)
        self.update_linenumbers()

    def highlight_tags(self, text):
        tag_pattern = r"<\/?(\w+)>"
        tags = re.findall(tag_pattern, text)
        keywords = ["html", "head", "body", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "a", "img", "table", "tr", "td", "th", "input", "form", "button", "label", "title"]

        for tag in tags:
            if tag.lower() in keywords:
                start = "1.0"
                while True:
                    start = self.text_widget.search(f"<{tag}>", start, stopindex="end", regexp=True)
                    if not start:
                        break
                    end = f"{start}+{len(tag)+2}c"
                    self.text_widget.tag_add("open_tag", start, end)
                    start = end

            close_tag = f"</{tag}>"
            start = "1.0"
            while True:
                start = self.text_widget.search(close_tag, start, stopindex="end", regexp=True)
                if not start:
                    break
                end = f"{start}+{len(close_tag)}c"
                self.text_widget.tag_add("close_tag", start, end)
                start = end

    def update_linenumbers(self, event=None):
        lines = self.text_widget.get("1.0", "end").split("\n")
        line_numbers = "\n".join(str(i) for i in range(1, len(lines) + 1))
        self.linenumbers.config(state="normal")
        self.linenumbers.delete("1.0", "end")
        self.linenumbers.insert("1.0", line_numbers)
        self.linenumbers.config(state="disabled")

    def update_syntax_highlight(self):
        self.highlight_syntax(None)

    def show_dom_tree(self):
        html_text = self.text_widget.get("1.0", "end")
        soup = BeautifulSoup(html_text, "html.parser")

        if not self.dom_viewer:
            self.dom_viewer = DOMViewer(self.master)
        self.dom_viewer.update_dom_tree(soup)

root = tk.Tk()
text = SyntaxHighlightText(root)
text.pack(side="right", fill="both", expand=True)

scrollbar = tk.Scrollbar(root, command=text.text_widget.yview)
scrollbar.pack(side="left", fill="y")
text.text_widget.config(yscrollcommand=scrollbar.set)

show_dom_button = tk.Button(root, text="Mostrar DOM", command=text.show_dom_tree)
show_dom_button.pack()

root.mainloop()


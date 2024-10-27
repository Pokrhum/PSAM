from flask import Flask, render_template_string, request
from markupsafe import Markup
import numpy as np
import pandas as pd
from utils import generate_filtered_graph
import urllib.parse
import gzip

app = Flask(__name__)

with gzip.open('PFAS_map.csv.gz', 'rt') as f:
    PFAS_map = pd.read_csv(f)

PFAS_map['date'] = pd.to_datetime(PFAS_map['date'], errors='coerce')

# Template HTML de base avec barre de navigation
base_html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        .navbar {
            overflow: hidden;
            background-color: #333;
            padding: 10px;
        }
        .navbar a {
            float: left;
            color: white;
            text-align: center;
            padding: 10px;
            text-decoration: none;
        }
        .navbar a:hover {
            background-color: #ddd;
            color: black;
        }
        .container {
            width: 80%;
            margin: auto;
            padding: 20px;
        }
         .map-container {
            width: 600px;
            height: 600px;
            margin: auto;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">Accueil</a>
        <a href="/carte">Carte de France</a>
        <a href="/recherche">Recherche</a>
    </div>
    <div class="container">
        {{ content|safe }}
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    content = """
        <h1>Bienvenue sur l'application PFAS</h1>
        <p>Veuillez sélectionner un site sur la carte pour voir les détails.</p>
        <p><a href="/carte">Voir la carte de France</a></p>
    """
    return render_template_string(base_html_template, title="Accueil", content=content)


@app.route("/carte")
def show_carte():
    # Calculer les informations générales du dataset
    total_sites = PFAS_map['name'].nunique()
    average_values_per_site = PFAS_map.drop_duplicates(subset=['date', 'name']).groupby('name')['value'].mean()
    sites_above_threshold = (average_values_per_site > 4).sum()
    average_value = average_values_per_site.mean()

    # Rendre un fichier HTML de la carte de France dans un conteneur de taille fixe avec des informations à droite
    content = f"""
        <h1>Carte de France</h1>
        <div style="display: flex;">
            <div class="map-container">
                <iframe src="/static/carte_france.html" width="100%" height="100%" style="border:none;"></iframe>
            </div>
            <div style="margin-left: 20px;">
                <h2>Informations Générales</h2>
                <p><strong>Nombre de sites :</strong> {total_sites}</p>
                <p><strong>Nombre de sites avec concentration > 4 ng/L :</strong> {sites_above_threshold}</p>
                <p><strong>Valeur moyenne de concentration :</strong> {average_value:.2f} ng/L</p>
            </div>
        </div>
    """
    return render_template_string(base_html_template, title="Carte de France", content=content)


@app.route("/recherche", methods=["GET", "POST"])
def search():
    search_results = ""
    if request.method == "POST":
        query = request.form.get("query")
        filtered_data = PFAS_map[PFAS_map["name"].str.contains(query, case=False, na=False)]

        if not filtered_data.empty:
            search_results = filtered_data[['date', 'value', 'less_than', 'name', 'source_text', 'unit', 'substance']].to_html(index=False, border=1)
        else:
            search_results = f"<p>Aucun site trouvé pour la recherche : '{query}'</p>"
    content = f"""
        <h1>Recherche de Sites</h1>
        <form method="post">
            <input type="text" name="query" placeholder="Rechercher un site par nom" required>
            <button type="submit">Rechercher</button>
        </form>
        <div style="margin-top: 20px;">
            {search_results}
        </div>
    """
    return render_template_string(base_html_template, title="Recherche", content=content)


@app.route("/details/<name>")
def show_details(name):
    filtered_data = PFAS_map[PFAS_map["name"] == name]

    # Création du nouveau DataFrame en groupant par la colonne 'date'
    filtered_data = filtered_data.groupby('date').agg(
        value=('value', 'sum'),
        unit=('unit', 'first'),
        less_than=('less_than', 'max'),
        source_text=('source_text', 'first')
    ).reset_index()

    # Si la somme de 'value' est égale à 0, la remplacer par NaN
    filtered_data['value'] = filtered_data['value'].apply(lambda x: np.nan if x == 0 else x)
    # Vérifier ligne par ligne si 'value' n'est pas NaN, alors 'less_than' doit être NaN
    filtered_data.loc[filtered_data['value'].notna(), 'less_than'] = np.nan

    # Utiliser la fonction pour générer le graphique interactif
    plot_html = generate_filtered_graph(filtered_data, name)

    # Convertir le nouveau tableau en HTML
    new_table_html = filtered_data.to_html(index=False, border=1)

    # Créer un tableau des différents PFAS retrouvés dans les analyses avec des liens hypertextes
    pfas_list = PFAS_map[PFAS_map["name"] == name]['substance'].unique()
    links = [f"<a href='/details/{urllib.parse.quote(name)}/{pfas}'>{pfas}</a>" for pfas in pfas_list]
    pfas_table_html = "<table border='1' style='margin-left: 20px;'><tr><th>Substance</th></tr>" + "".join(
        [f"<tr><td>{link}</td></tr>" for link in links]) + "</table>"

    pfas_table_html = Markup(pfas_table_html)

    # Contenu HTML de la page avec le graphique interactif
    content = f"""
        <h1>Détails pour {name}</h1>
        <div style="display: block; margin: auto;">
            {plot_html}
        </div>
        <h2 style="margin-top: 30px;">Données Utilisées</h2>
        <div style="float: left; width: 65%;">
            {new_table_html}
        </div>
        <div style="float: right; width: 30%;">
            <h3>Substances Testées</h3>
            {pfas_table_html}
        </div>
        <div style="clear: both; margin-top: 20px;">
            <a href="/carte" style="text-decoration: none; color: blue;">Retour à la carte</a>
        </div>
    """

    return render_template_string(base_html_template, title=f"Détails pour {name}", content=content)

@app.route("/details/<name>/<substance>")
def show_substance_details(name, substance):
    # Filtrer les données pour le nom et la substance spécifiés
    filtered_data = PFAS_map[(PFAS_map["name"] == name) & (PFAS_map["substance"] == substance)]

    # Utiliser la fonction pour générer le graphique interactif
    plot_html = generate_filtered_graph(filtered_data, f"{name} - {substance}")

    # Créer un tableau des données utilisées
    substance_table_html = filtered_data[['date', 'value', 'less_than', 'source_text', 'unit']].to_html(index=False, border=1)

    content = f"""
        <h1>Détails pour {substance} à {name}</h1>
        <div style="display: block; margin: auto;">
            {plot_html}
        </div>
        <h2 style="margin-top: 30px;">Données Utilisées</h2>
        <div style="margin-top: 20px;">
            {substance_table_html}
        </div>
        <div style="margin-top: 20px;">
            <a href='/details/{urllib.parse.quote(name)}' style='text-decoration: none; color: blue;'>Retour aux détails pour {name}</a>
        </div>
    """

    return render_template_string(base_html_template, title=f"Détails pour {substance} à {name}", content=content)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

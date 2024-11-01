from flask import Flask, render_template_string, request
from markupsafe import Markup
import pandas as pd
from utils import generate_filtered_graph
import urllib.parse
import gzip

app = Flask(__name__)

with gzip.open('PFAS_map.csv.gz', 'rt', encoding="utf-8") as f:
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
        .styled-button {
            display: inline-block;
            background-color: #6200ea;
            color: white;
            padding: 10px 20px;
            font-size: 1em;
            text-align: center;
            text-decoration: none;
            border-radius: 5px;
            transition: background-color 0.3s, transform 0.2s;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .styled-button:hover {
            background-color: #3700b3;
            transform: translateY(-2px);
            color: #ffffff;
        }
        .styled-button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        body {
            font-family: Arial, sans-serif;
            background-color: #f4f7f9;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .navbar {
            background-color: #6200ea;
            color: white;
            padding: 15px;
            width: 100%;
            display: flex;
            justify-content: center;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .navbar a {
            color: white;
            padding: 12px 20px;
            margin: 0 10px;
            text-decoration: none;
            font-weight: bold;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .navbar a:hover {
            background-color: #3700b3;
            color: #ffffff;
        }
        .container {
            width: 90%;
            max-width: 800px;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            margin-top: 30px;
        }
        h1 {
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            font-size: 1.1em;
        }
        button, input[type="text"] {
            padding: 10px 20px;
            font-size: 1em;
            border: none;
            border-radius: 5px;
            margin-top: 10px;
            outline: none;
            transition: background-color 0.3s, color 0.3s;
        }
        button {
            background-color: #6200ea;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #3700b3;
            color: #ffffff;
        }
        input[type="text"] {
            border: 1px solid #ddd;
            width: calc(100% - 22px);
            margin-top: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        .map-container {
            width: 100%;
            max-width: 600px;
            height: 400px;
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f4f7f9;
            color: #333;
        }

        /* Style général pour tous les liens hypertextes */
        a {
            color: #2a5d9f;
            text-decoration: none;
            font-weight: bold;
            transition: color 0.3s ease, text-shadow 0.3s ease;
        }
        a:hover {
            color: #3a7bd5;  /* Une couleur plus claire pour une meilleure lisibilité */
            text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.2);
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
        <p>Ce projet vise à surveiller et analyser la présence de substances perfluoroalkylées (PFAS) dans les eaux françaises.
        Les PFAS, connus sous le nom de "polluants éternels", sont des substances chimiques persistantes dans l'environnement
        et représentent un enjeu de santé publique en raison de leur toxicité potentielle.</p>
        <p>Grâce à cette application, vous pouvez explorer les niveaux de concentration de PFAS dans différents sites en France,
        afficher des graphiques d'évolution dans le temps et consulter des informations spécifiques pour chaque substance.</p>
        <p>
            <a href="/carte" class="styled-button">Voir la carte de France</a>
        </p>
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


from flask import request, render_template_string


@app.route("/recherche", methods=["GET", "POST"])
def search():
    search_results = ""
    if request.method == "POST":
        query = request.form.get("query")

        # Filtrer les données pour obtenir uniquement les noms uniques correspondant à la requête
        filtered_data = PFAS_map[PFAS_map["name"].str.contains(query, case=False, na=False)]['name'].unique()

        # Générer des liens hypertextes pour chaque site trouvé avec encodage des noms
        if filtered_data.size > 0:
            search_results = "<ul>" + "".join(
                [f"<li><a href='/details/{urllib.parse.quote(name)}'>{name}</a></li>" for name in filtered_data]
            ) + "</ul>"
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


    # Utiliser la fonction pour générer le graphique interactif
    plot_html, filtered_data = generate_filtered_graph(filtered_data, name)

    # Convertir le nouveau tableau en HTML
    mean_table_html = filtered_data.to_html(index=False, border=1)

    # Créer un tableau des différents PFAS retrouvés dans les analyses avec des liens hypertextes
    pfas_list = PFAS_map[PFAS_map["name"] == name][['substance', 'value']]
    pfas_list = pfas_list.groupby('substance')['value'].apply(list).to_dict()
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
            {mean_table_html}
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
    plot_html, filtered_data = generate_filtered_graph(filtered_data, f"{name} - {substance}")

    # Créer un tableau des données utilisées
    substance_table_html = filtered_data.to_html(index=False, border=1)

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

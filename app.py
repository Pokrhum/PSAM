import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import ScalarFormatter
import pandas as pd
import io
import base64
from flask import Flask, render_template_string, render_template

app = Flask(__name__)


PFOS_29_map = pd.read_csv("PFOS_29_map.csv")


@app.route("/")
def home():
    # Page d'accueil simple avec un message
    return """
           <h1>Bienvenue sur l'application PFOS</h1>
           <p>Veuillez sélectionner un site sur la carte pour voir les détails.</p>
           <p><a href="/carte">Voir la carte de France</a></p>
       """

@app.route("/carte")
def show_carte():
    # Rendre un fichier HTML de la carte de France
    return render_template("carte_france.html")

@app.route("/details/<name>")
@app.route("/details/<name>")
@app.route("/details/<name>")
@app.route("/details/<name>")
def show_details(name):
    # Filtrer les données pour le site spécifique
    filtered_data = PFOS_29_map[PFOS_29_map["name"] == name]

    # S'assurer que la colonne 'date' est de type datetime
    filtered_data['date'] = pd.to_datetime(filtered_data['date'], errors='coerce')
    filtered_data = filtered_data.dropna(subset=['date'])

    # Supprimer les colonnes inutiles pour simplifier l'affichage
    columns_to_keep = ['date', 'value', 'less_than', 'name', 'source_text', 'unit', 'pfas_sum']
    filtered_data = filtered_data[columns_to_keep]

    # Générer le graphique
    plt.figure(figsize=(10, 6))

    # Tracer les points pour les valeurs non-nulles de la concentration
    if 'value' in filtered_data.columns:
        plt.scatter(filtered_data['date'][filtered_data['value'].notna()],
                    filtered_data['value'][filtered_data['value'].notna()],
                    marker='+', c='b', label='Concentration en ng/L')

    # Tracer les points pour les valeurs du seuil de détection
    if 'less_than' in filtered_data.columns:
        plt.scatter(filtered_data['date'][filtered_data['less_than'].notna()],
                    filtered_data['less_than'][filtered_data['less_than'].notna()],
                    marker='+', c='g', label='Seuil de détection')

    # Ajouter une ligne rouge horizontale pour indiquer le seuil maximal pour la santé
    plt.axhline(y=4, color='red', linestyle='--', label='Seuil maximal pour la santé (4ng/L)')

    # Ajouter des titres et des labels aux axes
    plt.title(f"Évolution des PFOS dans le temps ({name})", fontsize=12)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Valeur par ng/L', fontsize=12)
    plt.legend()


    # Formater les étiquettes de l'axe Y pour éviter la notation scientifique
    plt.gca().yaxis.set_major_formatter(ScalarFormatter())
    plt.gca().ticklabel_format(style='plain', axis='y', useOffset=False)

    # Ajuster les étiquettes de l'axe X pour qu'elles apparaissent tous les 3 mois
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # Faire pivoter les étiquettes de date pour une meilleure lisibilité
    plt.xticks(rotation=45)
    plt.grid(linestyle=':')
    plt.tight_layout()

    # Convertir le graphique en image base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # Convertir le DataFrame filtré en HTML avec les colonnes pertinentes
    data_table_html = filtered_data.to_html(index=False, border=1)

    # Template HTML simplifié
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Détails pour {{ name }}</title>
    </head>
    <body>
        <div style="width: 80%; margin: auto; padding: 20px;">
            <h1>Détails pour {{ name }}</h1>
            <div>
                <img src="data:image/png;base64,{{ plot_url }}" alt="Graphique des valeurs" style="display: block; margin: auto;"/>
            </div>
            <h2 style="margin-top: 30px;">Données Utilisées</h2>
            <div>
                {{ data_table|safe }}
            </div>
            <div style="margin-top: 20px;">
                <a href="/carte" style="text-decoration: none; color: blue;">Retour à la carte</a>
            </div>
        </div>
    </body>
    </html>
    """

    return render_template_string(html_template, name=name, plot_url=plot_url, data_table=data_table_html)



if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)



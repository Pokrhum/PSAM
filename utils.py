import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

def generate_filtered_graph(filtered_data, name):

        # Générer le graphique
        plt.figure(figsize=(10, 6))

        if 'value' in filtered_data.columns:
            plt.scatter(filtered_data['date'][(filtered_data['value'].notna()) & (filtered_data['value'] != 0)],
                        filtered_data['value'][(filtered_data['value'].notna()) & (filtered_data['value'] != 0)],
                        marker='+', c='b', label='Concentration en ng/L')

        # Tracer les points pour les valeurs du seuil de détection
        if 'less_than' in filtered_data.columns:
            plt.scatter(filtered_data['date'][filtered_data['less_than'].notna()],
                        filtered_data['less_than'][filtered_data['less_than'].notna()],
                        marker='+', c='g', label='Seuil de détection')

        plt.axhline(y=4, color='red', linestyle='--', label='Seuil maximal pour la santé')
        plt.title(f"Évolution des PFAS dans le temps ({name})", fontsize=12)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Valeur par ng/L', fontsize=12)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(ScalarFormatter())
        plt.gca().ticklabel_format(style='plain', axis='y', useOffset=False)
        plt.xticks(rotation=45)
        plt.grid(linestyle=':')
        plt.tight_layout()
